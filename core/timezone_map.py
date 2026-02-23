"""
Минимальная карта 'Субъект РФ -> таймзона'.
Можно расширять. Для MVP: дефолт Europe/Moscow, плюс ключевые исключения.
"""
DEFAULT_TZ = "Europe/Moscow"

REGION_TZ = {
    "Калининградская область": "Europe/Kaliningrad",

    "Москва": "Europe/Moscow",
    "Московская область": "Europe/Moscow",
    "Санкт-Петербург": "Europe/Moscow",
    "Ленинградская область": "Europe/Moscow",

    "Самарская область": "Europe/Samara",

    "Свердловская область": "Asia/Yekaterinburg",
    "Тюменская область": "Asia/Yekaterinburg",
    "Челябинская область": "Asia/Yekaterinburg",
    "Пермский край": "Asia/Yekaterinburg",

    "Омская область": "Asia/Omsk",

    "Новосибирская область": "Asia/Novosibirsk",
    "Красноярский край": "Asia/Krasnoyarsk",
    "Кемеровская область": "Asia/Novokuznetsk",
    "Томская область": "Asia/Tomsk",

    "Иркутская область": "Asia/Irkutsk",

    "Республика Саха (Якутия)": "Asia/Yakutsk",
    "Амурская область": "Asia/Yakutsk",

    "Приморский край": "Asia/Vladivostok",
    "Хабаровский край": "Asia/Vladivostok",
    "Сахалинская область": "Asia/Sakhalin",

    "Магаданская область": "Asia/Magadan",
    "Камчатский край": "Asia/Kamchatka",
    "Чукотский автономный округ": "Asia/Anadyr",
}

def tz_for_region(region: str) -> str:
    region = (region or "").strip()
    return REGION_TZ.get(region, DEFAULT_TZ)
