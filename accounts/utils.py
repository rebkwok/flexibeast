# -*- coding: utf-8 -*-

from django.core.cache import cache


def active_data_privacy_cache_key(user):
    from accounts.models import DataPrivacyPolicy
    current_version = DataPrivacyPolicy.current_version()
    return 'user_{}_active_data_privacy_agreement_version_{}'.format(
        user.id, current_version
    )


def has_active_data_privacy_agreement(user):
    key = active_data_privacy_cache_key(user)
    if cache.get(key) is None:
        has_active_agreement = bool(
            [
                True for dp in user.data_privacy_agreement.all()
                if dp.is_active
            ]
        )
        cache.set(key, has_active_agreement, timeout=600)
    else:
        has_active_agreement = bool(cache.get(key))
    return has_active_agreement
