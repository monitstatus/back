import socket
import ssl
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime

import requests
from pythonping import ping
from requests.auth import HTTPBasicAuth

from app import schemas
from app.core import config
from app.models.monitor import Monitor
from app.schemas.monitor import MonitorTypeEnum



@dataclass
class MonitResponse:
    response_representation: str
    incident_cause: str
    response_time: float
    status: bool


def show_response_detail(response: requests.Response) -> str:
    detail_lines = [f"{response.status_code} {response.reason}", ""]
    for header in response.headers:
        detail_lines.append(f"{header}: {response.headers[header]}")
    return '\n'.join(detail_lines)


def get_num_days_before_expired(hostname: str, port: str = '443') -> int:
    """
    Get number of days before a TLS/SSL of a domain expires
    """
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port)) as sock:
        with context.wrap_socket(sock, server_hostname=hostname) as ssock:
            ssl_info = ssock.getpeercert()
            expiry_date = datetime.strptime(ssl_info['notAfter'], '%b %d %H:%M:%S %Y %Z')
            delta = expiry_date - datetime.utcnow()
            return delta.days


def http_monitoring(monitor: Monitor) -> MonitResponse:
    incident_cause = ''
    response_representation = ''
    try:
        headers = {'User-Agent': config.USER_AGENT}
        if monitor.request_headers:
            headers = {**headers, **monitor.request_headers}

        authentication = None
        if monitor.auth_user and monitor.auth_pass:
            authentication = HTTPBasicAuth(monitor.auth_user, monitor.auth_pass)

        requester = requests.request
        if monitor.keep_cookies_between_redirects:
            requester = requests.Session().request

        response = requester(
            method=monitor.http_method,
            url=monitor.endpoint,
            timeout=monitor.request_timeout,
            verify=monitor.verify_ssl,
            allow_redirects=monitor.follow_redirects,
            headers=headers,
            data=monitor.request_body,
            auth=authentication,
        )
        response_time = response.elapsed.total_seconds()
        response_representation = show_response_detail(response)

        if monitor.alert_type == schemas.AlertTypeEnum.unavailable:
            status = response.ok
            if not status:
                incident_cause = f"HTTP {response.status_code} - {response.reason}"
        elif monitor.alert_type == schemas.AlertTypeEnum.does_not_contain_keyword:
            status = response.text.find(monitor.keyword) != -1
            if not status:
                incident_cause = "Keyword not found"
        elif monitor.alert_type == schemas.AlertTypeEnum.contains_keyword:
            status = response.text.find(monitor.keyword) == -1
            if not status:
                incident_cause = "Keyword found"
        else:
            raise Exception(f"Unknown alert type for monitor.id={monitor.id}")
    except requests.exceptions.Timeout:
        incident_cause = 'Timeout'
        response_time = 0
        status = False
    except requests.exceptions.ConnectionError as exception:
        incident_cause = 'Connection Error'
        if "[Errno -2] Name or service not known" in str(exception):
            incident_cause = 'DNS lookup failure'
        response_time = 0
        status = False
    except requests.exceptions.TooManyRedirects:
        incident_cause = 'Too Many Redirects'
        response_time = 0
        status = False

    if status and monitor.ssl_check_expiration:
        parsed_url = urllib.parse.urlparse(monitor.endpoint)
        if parsed_url.scheme == 'https':
            days_to_expiration = get_num_days_before_expired(parsed_url.netloc)
            if days_to_expiration <= monitor.ssl_check_expiration:
                return MonitResponse(
                    response_representation,
                    f'SSL certificate expires in {days_to_expiration} days',
                    response_time,
                    False
                )

    return MonitResponse(
        response_representation,
        incident_cause,
        response_time,
        status
    )


def ping_monitoring(monitor: Monitor) -> MonitResponse:
    r = ping(
        monitor.endpoint,
        timeout=monitor.request_timeout / monitor.num_pings,
        count=monitor.num_pings,
    )

    incident_cause = ''
    if not r.success():
        incident_cause = [r for r in r._responses if not r.success][0].legacy_repr()

    return MonitResponse(
        repr(r),
        incident_cause,
        r.rtt_avg_ms,
        r.success(),
    )


def _socket_monitoring(monitor: Monitor, socket_kind: socket.SocketKind) -> MonitResponse:
    try:
        with socket.socket(socket.AF_INET, socket_kind) as s:
            s.settimeout(monitor.request_timeout)
            start = time.time()
            s.connect((monitor.endpoint, monitor.port))
            if monitor.data:
                s.sendall(bytes(monitor.data, 'utf-8'))
            response = s.recv(1024)
            end = time.time()
            elapsed_time = end - start
    except ConnectionRefusedError:
        return MonitResponse('', 'Connection refused', 0, False)
    except TimeoutError:
        return MonitResponse('', 'Timeout', 0, False)

    str_response = response.decode()

    status = True
    incident_cause = ''
    if monitor.alert_type == schemas.AlertTypeEnum.does_not_contain_keyword:
        status = str_response.find(monitor.keyword) != -1
        if not status:
            incident_cause = "Keyword not found"

    return MonitResponse(
        str_response,
        incident_cause,
        elapsed_time,
        status,
    )


def tcp_monitoring(monitor: Monitor) -> MonitResponse:
    return _socket_monitoring(monitor, socket.SOCK_STREAM)


def udp_monitoring(monitor: Monitor) -> MonitResponse:
    return _socket_monitoring(monitor, socket.SOCK_DGRAM)


def check_monitor(monitor):
    if monitor.monitor_type == MonitorTypeEnum.http:
        return http_monitoring(monitor)

    elif monitor.monitor_type == MonitorTypeEnum.ping:
        return ping_monitoring(monitor)

    elif monitor.monitor_type == MonitorTypeEnum.tcp:
        return tcp_monitoring(monitor)

    elif monitor.monitor_type == MonitorTypeEnum.udp:
        return udp_monitoring(monitor)

    raise NotImplementedError
