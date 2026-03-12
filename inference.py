import pickle
import torch

from transformers import AutoTokenizer, AutoModelForSequenceClassification

from parsing import get_processed_vacancy, CATEGORICAL_COLUMNS
from models import BERTSalaryPredictor


name_to_tokenizer = {}
name_to_model = {}

def load_model_and_tokenizer(model_info: dict) -> None:
    global name_to_model, name_to_tokenizer

    model_name = model_info['model_name']
    huggingface_model_name = model_info['huggingface_model_name']
    num_labels = model_info['num_labels']

    huggingface_model_path = f'../weights/huggingface_models/'
    main_model_path = f'../weights/salary_prediction_models/{model_name}.weights'

    if model_name not in name_to_tokenizer:
        name_to_tokenizer[model_name] = AutoTokenizer.from_pretrained(huggingface_model_name, cache_dir=huggingface_model_path)

    if model_name not in name_to_model:
        huggingface_model = AutoModelForSequenceClassification.from_pretrained(huggingface_model_name, cache_dir=huggingface_model_path, num_labels=num_labels)

        name_to_model[model_name] = BERTSalaryPredictor(bert=huggingface_model, hid_size=num_labels)
        name_to_model[model_name].load_state_dict(torch.load(main_model_path, map_location='cpu'))


async def get_salary(vacancy_id: str, model_info: dict) -> float:
    vacancy = await get_processed_vacancy(vacancy_id)

    with open('../serialized/categorical_vectorizer.pkl', 'rb') as file:
        categorical_vectorizer = pickle.load(file)

    load_model_and_tokenizer(model_info)

    model_name = model_info['model_name']
    tokenizer = name_to_tokenizer[model_name]
    model = name_to_model[model_name]

    model_input = {'name_and_description': tokenizer([vacancy['name'] + '; ' + vacancy['description']], 
                                                        padding=True, truncation=True, max_length=512, return_tensors="pt"), 
                    'categorical': torch.from_numpy(categorical_vectorizer.transform({key: vacancy[key] for key in CATEGORICAL_COLUMNS}))}

    log1p_salary = model(model_input)
    salary = (torch.exp(log1p_salary) - 1).item()
    return salary