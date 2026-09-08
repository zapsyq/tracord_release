from fastapi_mail import FastMail, ConnectionConfig
from pydantic import SecretStr
from app.config import mail_config

def create_mail():
    mail_setting = ConnectionConfig(
        MAIL_USERNAME=mail_config.mail_username,
        MAIL_PASSWORD=SecretStr(mail_config.mail_password),
        MAIL_FROM=mail_config.mail_from,
        MAIL_PORT=mail_config.mail_port,
        MAIL_SERVER=mail_config.mail_server,
        MAIL_STARTTLS=mail_config.mail_starttls,
        MAIL_SSL_TLS=mail_config.mail_ssl,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True
    )
    return FastMail(mail_setting)
