import pandas as pd
import os
import glob

import warnings


class DATA:
    def __init__(self):
        self.metrics = []
        self.units = {}


    @staticmethod
    def prepare_data(folder_path='../data/source/temp',
                     out_file='../data/processed/temp.xlsx') -> pd.DataFrame():
        """
            Подготавливает данные CSV файлов из папки temp/
        """
        if not os.path.isdir(folder_path):
            raise ValueError(f"Folder '{folder_path}' does not exist or is not a directory")

        files = glob.glob(os.path.join(folder_path, '*.csv'))

        if not files:
            warnings.warn(f"No CSV files found in folder: {folder_path}")
            return pd.DataFrame()

        print(f"Found {len(files)} CSV files in folder: {folder_path}")

        list_of_dfs = []
        for f in files:
            df = pd.read_csv(f)
            list_of_dfs.append(df)
        df = pd.concat(list_of_dfs, ignore_index=True)
        print(f"Lenfth of raw dataframe: {len(df)}")

        # Обрабатываем колонки нового файла
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], format='%d.%m.%y %H:%M:%S', errors='coerce')
        df = df.sort_values(by=['VM', 'Metric', 'Timestamp'], ascending=[True, True, True])

        # ['VM', 'Metric', 'Timestamp'] является индексом в базе данных. Они не должны дублироваться
        df = df.drop_duplicates(subset=['VM', 'Metric', 'Timestamp'], keep='last')

        # Оставляем только колонки 'vm', 'timestamp', 'metric', 'value' для занесения в базу с фактами
        df.drop(columns=['Unit', 'Date', 'Time'], inplace=True)
        df.rename(columns={'VM': 'vm',
                            'Timestamp': 'timestamp',
                            'Metric': 'metric',
                            'Value': 'value'}, inplace=True)

        print(f"Length of dataframe after dropping duplicates: {len(df)}")
        # Сохраняем результат
        try:
            df.to_excel(out_file, index=False)
            print(f"Data saved to {out_file}")
        except Exception as e:
            print(f"Error saving to Excel: {e}")

        return df


    def pivot_metrics(data_path="data/data.csv",
                     out_path="data/Сводная таблица по метрикам.xlsx"
                     ) -> pd.DataFrame:
        """
        processes csv file with metrics
        :param data_path: path to file with data for all servers
        :param out_path: path to save processed data
        :return: pivot table with all metrics for servers
        """
        try:
            # columns = ['VM_Name', 'vCenter', 'Metric', 'Value', 'Unit', 'Timestamp', 'Date', 'Time']
            df = pd.read_csv(data_path)
        except Exception as e:
            print(f"Ошибка при чтении файла: {e}")
            return pd.DataFrame()

        df_wide = df.pivot_table(
            index=['VM_Name', 'vCenter', 'Timestamp'],
            columns='Metric',
            values='Value',
            aggfunc='first'  # на случай дублей
        ).reset_index()

        df_wide = df_wide.sort_values(['VM_Name', 'vCenter', 'Timestamp']).reset_index(drop=True)
        df_wide.to_excel(out_path)
        return df_wide


if __name__ == '__main__':
    # Создаем объект класса DATA для подготовки данных для работы из исходников
    data = DATA()

    # 1. Готовим данные значений метрик выгруженные по 20 серверам за период: с 25-11-2025 по 01-12-2025
    # Папка с данными data/temp собранный датафрейм сохраняется в файл temp.xlsx
    df = data.prepare_data(folder_path='../data/source/temp',
                           out_file='../data/processed/25-11-2025_01-12-2025.xlsx')

    # 2. Далее создаем сводную таблицу по этим серверам и метрикам
    # df_wide = data.pivot_metrics()

    # 3. Готовим данные по

