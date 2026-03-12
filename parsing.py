import re
import aiohttp

from random_user_agent.user_agent import UserAgent
from random_user_agent.params import SoftwareName, OperatingSystem

from html2text import html2text


SOFTWARE_NAMES = [SoftwareName.CHROME.value]
OPERATING_SYSTEMS = [OperatingSystem.WINDOWS.value, OperatingSystem.LINUX.value]
USER_AGENT = UserAgent(software_names=SOFTWARE_NAMES, operating_systems=OPERATING_SYSTEMS, limit=100)

VACANCY_URL = "https://api.hh.ru/vacancies/{}"


def get_vacancy_id_from_url(url: str) -> str:
    return re.search(pattern='[0-9]+', string=url).group(0)


async def get_vacancy(id_: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(VACANCY_URL.format(id_), 
                                headers={'User-Agent': USER_AGENT.get_random_user_agent()}, 
                                timeout=20) as resp:
            return await resp.json()


REQUIRED_COLUMNS = ['id',
                    'billing_type',
                    'name',
                    'response_letter_required',
                    'area',
                    'salary',
                    'allow_messages',
                    'experience',
                    'schedule',
                    'employment',
                    'description',
                    'accept_handicapped',
                    'accept_kids',
                    'driver_license_types',
                    'accept_incomplete_resumes',
                    'employer',
                    'has_test',
                    'accept_temporary']

TEXT_COLUMNS = ['name', 'description']
CATEGORICAL_COLUMNS = ['billing_type',
                        'response_letter_required',
                        'area',
                        'allow_messages',
                        'experience',
                        'schedule',
                        'employment',
                        'accept_handicapped',
                        'accept_kids',
                        'accept_incomplete_resumes',
                        'employer',
                        'has_test',
                        'accept_temporary']


def set_name_to_fields(vacancy: dict, fields: list[str]) -> dict:
    for field in fields:
        vacancy[field] = vacancy[field]['name']
    return vacancy


def filter_columns(vacancy: dict, required_columns: list[str]) -> dict:
    for key in list(vacancy.keys()):
        if key not in required_columns:
            vacancy.pop(key)
    return vacancy


async def get_processed_vacancy(vacancy_id: str) -> dict:
    vacancy = await get_vacancy(vacancy_id)
    vacancy = filter_columns(vacancy, REQUIRED_COLUMNS)
    vacancy = set_name_to_fields(vacancy, ['billing_type', 
                                           'area', 
                                           'experience', 
                                           'schedule', 
                                           'employment', 
                                           'employer'])
    vacancy['description'] = html2text(vacancy['description'])
    if len(vacancy['driver_license_types']) > 0:
        vacancy['description'] += '\n\nОпыт вождения: права категории ' + \
            ','.join(sorted(category['id'] for category in vacancy['driver_license_types'])) + '.'

    return vacancy

