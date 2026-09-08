#发送验证码的邮箱配置: 从 .env 读取
import os
from dotenv import load_dotenv

load_dotenv()

mail_username = os.getenv("MAIL_USERNAME", "")
mail_password = os.getenv("MAIL_PASSWORD", "")
mail_from = os.getenv("MAIL_FROM", mail_username)
mail_port = int(os.getenv("MAIL_PORT", "465"))
mail_server = os.getenv("MAIL_SERVER", "smtp.qq.com")
mail_starttls = os.getenv("MAIL_STARTTLS", "False").lower() == "true"
mail_ssl = os.getenv("MAIL_SSL", "True").lower() == "true"
