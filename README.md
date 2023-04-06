# Monitorstatus backend

## Stripe devenv

Install stripe cli and test with `stripe login` and

```
stripe listen --forward-to localhost:8000/billing/webhook
```

## Database operation tips

### Rebuild

```
make rebuild-db
```

### Generate and apply a migration

```
$ docker compose exec web alembic revision --autogenerate -m "Migration message"
[..]
  Generating /app/alembic/versions/4f194303db8f_migration_message_.py ...  done

$ docker compose exec web alembic upgrade head
Creating back_web_run ... done
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade 703bd77c5625 -> 4f194303db8f, Migration message
```

## Sendgrid

### Initial template creation

The Sendgrid email templates can be created by setting the sendgrid api key in the .env file and executing:

```
$ docker compose exec web python3 app/core/generate_sendgrid_templates.py
```

Make sure that the api key has access to the template engine.
This will create a few templates on sendgrid and print a few envvars that you should copy to your .env file.

> :warning: **This operation is not idempotent nor takes into account the existing templates**: Be careful here, every execution will create a few new templates!
