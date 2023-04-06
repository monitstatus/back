import stripe

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.api import deps
from app.core import config


router = APIRouter(prefix="/billing")
stripe.api_key = config.STRIPE_SECRET_KEY


# @router.get('/config')
# def get_publishable_key():
#     return {'public_key': config.STRIPE_PUBLISHABLE_KEY}


@router.get('/stripe/portal')
def get_portal_session(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_user),
):
    db_customer = crud.customer.get_by_user_id(db, user_id=current_user.id)
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    portal = stripe.billing_portal.Session.create(
        customer=db_customer.stripe_customer_id,
        return_url=f"{config.FRONT_BASE_URL}/user",
    )
    return {'url': portal['url']}


# Fetch the Checkout Session to display the JSON result on the success page
@router.get('/stripe/checkout-session', response_model=stripe.checkout.Session)
def get_checkout_session(
    session_id : str,
    current_user: models.User = Depends(deps.get_current_user)
):
    checkout_session = stripe.checkout.Session.retrieve(session_id)
    return checkout_session


# test with `stripe login` and `stripe listen --forward-to localhost:8080/billing/webhook`
@router.post('/webhook')
async def webhook_received(
    request : Request,
    db: Session = Depends(deps.get_db),
    stripe_signature: str = Header(str)
):
    # You can use webhooks to receive information about asynchronous payment events.
    # For more about our webhook events check out https://stripe.com/docs/webhooks.
    webhook_secret = config.STRIPE_WEBHOOK_SECRET
    data = await request.body()

    # Retrieve the event by verifying the signature using the raw body and secret
    try:
        event = stripe.Webhook.construct_event(
            payload=data, sig_header=stripe_signature, secret=webhook_secret
        )
        event_data = event['data']
    except Exception as e:
        raise e
    # Get the type of webhook event sent - used to check the status of PaymentIntents.
    event_type = event['type']
    data_object = event_data['object']

    if event_type == 'checkout.session.completed':
        print('🔔 Checkout session completed')
        user_id = data_object['client_reference_id']
        stripe_customer_id = data_object['customer']

        session = stripe.checkout.Session.retrieve(
            data_object['id'], expand=['line_items'])
        plan_price_id = session.line_items['data'][0]['price']['id']

        print(user_id, stripe_customer_id, plan_price_id)
        db_customer = crud.customer.get_by_user_id(db, user_id=user_id)
        updated_customer = schemas.user.CustomerUpdate(
            user_id=user_id,
            stripe_customer_id=stripe_customer_id,
            plan_price_id=plan_price_id
        )
        crud.customer.update(db=db, db_obj=db_customer, obj_in=updated_customer)
    elif event_type == 'customer.subscription.created':
        print('🔔 Subscription created!')
    elif event_type == 'customer.subscription.updated':
        print('🔔 Subscription updated!')
        stripe_customer_id = data_object['customer']
        plan_price_id = data_object['plan']['id']
        db_customer = crud.customer.get(db, id=stripe_customer_id)
        updated_customer = schemas.user.CustomerUpdate(
            stripe_customer_id=stripe_customer_id,
            plan_price_id=plan_price_id,
        )
        crud.customer.update(db=db, db_obj=db_customer, obj_in=updated_customer)
    elif event_type == 'customer.subscription.deleted':
        print('🔔 Subscription deleted!')
        stripe_customer_id = data_object['customer']
        crud.customer.remove(db=db, id=stripe_customer_id)
        # TODO update and set as only basic again? or directly mark user as unexistent

    else:
        print(f'unhandled event: {event_type}')

    return {'status': 'success'}
