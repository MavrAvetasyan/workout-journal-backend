from __future__ import annotations

from datetime import datetime

import httpx

from .config import APP_LOGIN_URL, APP_NAME, MAIL_FROM, MAIL_PROVIDER, MAIL_REPLY_TO, RESEND_API_KEY


def _build_login_code_subject(code: str) -> str:
    return f"{APP_NAME}: код входа {code}"


def _build_login_code_text(code: str, expires_minutes: int) -> str:
    lines = [
        f"{APP_NAME}",
        "",
        "Ваш код для входа:",
        code,
        "",
        f"Код действует {expires_minutes} минут.",
    ]
    if APP_LOGIN_URL:
        lines.extend(["", f"Открыть приложение: {APP_LOGIN_URL}"])
    lines.extend(["", f"Отправлено: {datetime.utcnow().isoformat()}Z"])
    return "\n".join(lines)


def _build_login_code_html(code: str, expires_minutes: int) -> str:
    login_link = (
        f"""
        <div style="margin-top:24px;">
          <a href="{APP_LOGIN_URL}" style="display:inline-block;padding:14px 22px;border-radius:14px;background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#ffffff;text-decoration:none;font-weight:700;">
            Открыть приложение
          </a>
        </div>
        """
        if APP_LOGIN_URL
        else ""
    )
    return f"""
<!doctype html>
<html lang="ru">
  <body style="margin:0;padding:0;background:#eef3ff;font-family:Arial,Helvetica,sans-serif;color:#13203a;">
    <div style="max-width:560px;margin:0 auto;padding:32px 18px;">
      <div style="background:linear-gradient(180deg,#ffffff 0%,#f7faff 100%);border-radius:28px;padding:32px;box-shadow:0 20px 60px rgba(37,99,235,0.10);border:1px solid rgba(37,99,235,0.08);">
        <div style="font-size:12px;letter-spacing:0.12em;text-transform:uppercase;color:#2563eb;font-weight:700;">{APP_NAME}</div>
        <h1 style="margin:12px 0 10px;font-size:32px;line-height:1.1;">Ваш код для входа</h1>
        <p style="margin:0 0 24px;font-size:17px;line-height:1.6;color:#5d6b86;">
          Введите этот код в приложении, чтобы подтвердить вход.
        </p>
        <div style="padding:18px 20px;border-radius:22px;background:#f3f7ff;border:1px solid rgba(37,99,235,0.08);text-align:center;">
          <div style="font-size:12px;letter-spacing:0.2em;text-transform:uppercase;color:#6a7a98;">код</div>
          <div style="margin-top:8px;font-size:42px;line-height:1;font-weight:800;color:#0f172a;letter-spacing:0.22em;">{code}</div>
        </div>
        <p style="margin:22px 0 0;font-size:15px;line-height:1.6;color:#5d6b86;">
          Код действует <strong>{expires_minutes} минут</strong>. Если это были не вы, просто проигнорируйте письмо.
        </p>
        {login_link}
      </div>
    </div>
  </body>
</html>
"""


def send_login_code_email(*, email: str, code: str, expires_minutes: int) -> None:
    subject = _build_login_code_subject(code)
    text = _build_login_code_text(code, expires_minutes)
    html = _build_login_code_html(code, expires_minutes)

    if MAIL_PROVIDER == "resend" and RESEND_API_KEY:
        with httpx.Client(timeout=15.0) as client:
            payload = {
                "from": MAIL_FROM,
                "to": [email],
                "subject": subject,
                "text": text,
                "html": html,
            }
            if MAIL_REPLY_TO:
                payload["reply_to"] = MAIL_REPLY_TO
            response = client.post(
                "https://api.resend.com/emails",
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            response.raise_for_status()
            return

    print("=" * 60)
    print("MAIL DELIVERY FALLBACK")
    print(f"To: {email}")
    print(f"Subject: {subject}")
    print(text)
    print("=" * 60)
