from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

from django.core.mail import send_mail
from django.conf import settings

def send_verification_code(email, code):
    subject = 'Подтверждение регистрации на Akatsuki Soap'
    message = f'Ваш код подтверждения: {code}\nКод действителен 10 минут.'
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

def send_master_request_approved_email(request_id):
    from .models import MasterRequest
    request = MasterRequest.objects.select_related('client').get(id=request_id)
    subject = 'Ваша заявка на роль мастера одобрена'
    message = (
        f'Здравствуйте, {request.client.profile.fio}!\n\n'
        f'Поздравляем! Ваша заявка на роль мастера одобрена.\n'
        f'Теперь вы можете создавать свои мастер-классы на нашем сайте.\n\n'
        f'Комментарий администратора: {request.admin_comment or "нет"}\n\n'
        f'С уважением, Akatsuki Soap.'
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [request.client.email], fail_silently=False)


def send_master_request_rejected_email(request_id):
    from .models import MasterRequest
    request = MasterRequest.objects.select_related('client').get(id=request_id)
    subject = 'Ваша заявка на роль мастера отклонена'
    message = (
        f'Здравствуйте, {request.client.profile.fio}!\n\n'
        f'К сожалению, ваша заявка на роль мастера была отклонена.\n\n'
        f'Комментарий администратора: {request.admin_comment or "нет"}\n\n'
        f'Вы можете подать заявку повторно, если исправите замечания.\n\n'
        f'С уважением, Akatsuki Soap.'
    )
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [request.client.email], fail_silently=False)


def send_masterclass_moderation_email(masterclass_id, new_status):
    from .models import MasterClass
    try:
        mc = MasterClass.objects.select_related('master').get(id=masterclass_id)
    except MasterClass.DoesNotExist:
        return

    subject = f'Статус мастер-класса "{mc.name}" изменён'
    if new_status == 3:
        message = f'Ваш мастер-класс "{mc.name}" одобрен и опубликован.'
    else:
        message = f'Ваш мастер-класс "{mc.name}" отклонён. Комментарий: {mc.comment}'

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [mc.master.email],
        fail_silently=False,
    )


# ==================== НОВЫЕ ЗАДАЧИ ДЛЯ ЗАПИСИ НА МК ====================

def send_confirmation_email(signup_id):
    from .models import SignUpClass
    from django.urls import reverse
    signup = SignUpClass.objects.select_related(
        'client', 'session', 'session__masterclass', 'session__masterclass__master'
    ).get(id=signup_id)
    client = signup.client
    session = signup.session
    mc = session.masterclass
    master_profile = mc.master.profile
    subject = f'Заявка на мастер-класс "{mc.name}" принята'
    message = f"""
Здравствуйте, {client.profile.fio}!

Вы подали заявку на мастер-класс "{mc.name}".

Выбранное время: {session.date_event} {session.time_event}
Мастер: {master_profile.fio}, тел: {master_profile.phone}
Адрес: {mc.address}

Ваша заявка будет рассмотрена мастером. В ближайшее время вы получите письмо с подтверждением или отказом.

С уважением,
Akatsuki Soap
"""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [client.email], fail_silently=False)


def send_signup_approved_email(signup_id):
    from .models import SignUpClass
    signup = SignUpClass.objects.select_related(
        'client', 'session', 'session__masterclass', 'session__masterclass__master'
    ).get(id=signup_id)
    client = signup.client
    session = signup.session
    mc = session.masterclass
    master = mc.master.profile
    subject = f'Запись на мастер-класс "{mc.name}" подтверждена'
    message = f"""
Здравствуйте, {client.profile.fio}!

Ваша заявка на мастер-класс "{mc.name}" одобрена мастером.

Детали:
Дата: {session.date_event}
Время: {session.time_event}
Адрес: {mc.address}
Мастер: {master.fio}, тел: {master.phone}, email: {mc.master.email}

Если у вас возникли вопросы, свяжитесь с мастером.

Ждём вас!
"""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [client.email], fail_silently=False)


def send_signup_rejected_email(signup_id):
    from .models import SignUpClass
    signup = SignUpClass.objects.select_related(
        'client', 'session', 'session__masterclass'
    ).get(id=signup_id)
    client = signup.client
    session = signup.session
    mc = session.masterclass
    subject = f'Запись на мастер-класс "{mc.name}" отклонена'
    message = f"""
Здравствуйте, {client.profile.fio}!

К сожалению, ваша заявка на мастер-класс "{mc.name}" отклонена мастером.
Причина: {signup.master_comment or 'не указана'}

Вы можете выбрать другое время или связаться с мастером для уточнения.
"""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [client.email], fail_silently=False)


def send_thank_you_email(signup_id):
    from .models import SignUpClass
    signup = SignUpClass.objects.select_related(
        'client', 'session', 'session__masterclass'
    ).get(id=signup_id)
    client = signup.client
    session = signup.session
    mc = session.masterclass
    subject = f'Спасибо за посещение мастер-класса "{mc.name}"!'
    message = f"""
Здравствуйте, {client.profile.fio}!

Благодарим вас за посещение мастер-класса "{mc.name}".
Надеемся, вам понравилось!

Вы можете оставить отзыв на нашем сайте.

Ждём вас снова!
"""
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [client.email], fail_silently=False)