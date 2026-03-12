import sqlite3

class BotDatabaseHandler:
    def __init__(self, query_database_name: str) -> None:
        self.connection = sqlite3.connect(query_database_name)
        self.cursor = self.connection.cursor()
    

    def get_query_history(self, user_id: int) -> str:
        self.cursor.execute(f'SELECT VacancyId, ModelName, PredictedSalary From Queries ' + \
                            f'INNER JOIN Models ON Queries.ModelId = Models.ModelId WHERE UserId = {user_id}')
        queries = ['-- вакансия: https://rabota.by/vacancy/' + vacancy_id + \
                   f', выбранная модель: {model_name}'  + \
                   f', предсказанная заработная плата: {predicted_salary}.' 
                   for vacancy_id, model_name, predicted_salary in self.cursor.fetchall()]
        return '\n'.join(queries)
    

    def get_models(self) -> str:
        self.cursor.execute(f'SELECT ModelName From Models')
        model_names = self.cursor.fetchall()
        models = ['-- ' + model[0] + ('.' if i == len(model_names) - 1 else ',') for i, model in enumerate(model_names)]
        return '\n'.join(models)
    

    def get_id_from_model_name(self, model_name: str) -> int:
        self.cursor.execute(f'SELECT ModelId From Models WHERE ModelName = \'{model_name}\'')
        result = self.cursor.fetchall()
        if not result:
            return -1
        return result[0][0]
    

    def get_model_info_from_id(self, model_id: int) -> dict:
        self.cursor.execute(f'SELECT ModelName, HuggingFaceModelName, NumLabels From Models WHERE ModelId = {model_id}')
        model_name, huggingface_model_name, num_labels = self.cursor.fetchall()[0]
        return {'model_name': model_name, 'huggingface_model_name': huggingface_model_name, 'num_labels': num_labels}
    

    def get_model_name_from_id(self, model_id: int) -> str:
        self.cursor.execute(f'SELECT ModelName From Models WHERE ModelId = {model_id}')
        return self.cursor.fetchall()[0][0]
    

    def get_model_id_from_user_id(self, user_id: int) -> str:
        self.cursor.execute(f'SELECT ModelId From Users WHERE UserId = {user_id}')
        return self.cursor.fetchall()[0][0]


    def get_model_name_from_user_id(self, user_id: int) -> str:
        model_id = self.get_model_id_from_user_id(user_id)
        model_name = self.get_model_name_from_id(model_id)
        return model_name
    

    def set_user_model_id(self, user_id: int, model_id: int) -> None:
        self.cursor.execute(f'''
            UPDATE Users
            SET ModelId = {model_id}
            WHERE UserId = {user_id}
            ''')
        self.connection.commit()


    def add_user(self, user_id: int, model_id: int = 0) -> None:
        self.cursor.execute(f'''
            INSERT OR IGNORE INTO Users (UserId, ModelId) 
            VALUES(?, ?)
            ''', (user_id, model_id))
        self.connection.commit()
    

    def add_query_info(self, user_id: int, vacancy_id: str, model_id: int, predicted_salary: float) -> None:
        self.cursor.execute(f'''
            INSERT INTO Queries (UserId, VacancyId, ModelId, PredictedSalary)
            VALUES (?, ?, ?, ?)
            ''', (user_id, vacancy_id, model_id, predicted_salary))
        self.connection.commit()


    def clear_history(self, user_id: int) -> None:
        self.cursor.execute(f'DELETE FROM Queries WHERE UserId = {user_id}')
        self.connection.commit()


    def teardown(self) -> None:
        self.cursor.close()
        self.connection.close()
