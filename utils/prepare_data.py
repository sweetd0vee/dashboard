import pandas as pd
import os
import glob

import warnings


class DATA:
    def __init__(self):
        # Все 16 метрик встречающихся в данных
        self.metrics = [
            # CPU метрики
            'cpu.ready.summation', 'cpu.usage.average', 'cpu.usagemhz.average',
            # Disk метрики
            'disk.maxtotallatency.latest', 'disk.provisioned.latest',
            'disk.unshared.latest', 'disk.usage.average', 'disk.used.latest',
            # Memory метрики
            'mem.consumed.average', 'mem.overhead.average','mem.swapinrate.average',
            'mem.swapoutrate.average', 'mem.usage.average', 'mem.vmmemctl.average',
            # Метрики Сети
            'net.usage.average',
            # Системные метрики
            'sys.uptime.latest']
        self.units = {
            'cpu.ready.summation' : '',
            'cpu.usage.average': '',
            'cpu.usagemhz.average': '',
            'disk.maxtotallatency.latest': '',
            'disk.provisioned.latest': '',
            'disk.unshared.latest': '',
            'disk.usage.average': '',
            'disk.used.latest': '',
            'mem.consumed.average': '',
            'mem.overhead.average': '',
            'mem.swapinrate.average': '',
            'mem.swapoutrate.average': '',
            'mem.usage.average': '',
            'mem.vmmemctl.average': '',
            'net.usage.average': '',
            'sys.uptime.latest': ''

        }


    @staticmethod
    def process_temp(folder_path='../data/source/temp',
                     out_file='../data/processed/temp.xlsx') -> pd.DataFrame():
        """
            Подготавливает данные CSV файлов из папки temp/ по серверам за период: с 25-11-2025 по 01-12-2025 (включительно)
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

        # ['vm', 'metric', 'timestamp'] является индексом в базе данных. Они не должны дублироваться
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


    @staticmethod
    def process_data(in_file='../data/source/data.csv',
                     out_file='../data/processed/data.xlsx') -> pd.DataFrame():
        """
        Подготавливаем данные по серверам за период: с 04-12-2025 по 07-12-2025 (включительно)
        """
        df = pd.read_csv(in_file)
        print(f"Length of initial dataframe: {len(df)}")

        df.drop(columns=['vCenter', 'Unit', 'Date', 'Time'], inplace=True)
        df.rename(columns={
            'VM_Name': 'vm',
            'Metric': 'metric',
            'Value': 'value',
            'Timestamp': 'timestamp'
        }, inplace=True)

        # ['vm', 'metric', 'timestamp'] является индексом в базе данных. Они не должны дублироваться
        df = df.drop_duplicates(subset=['vm', 'metric', 'timestamp'], keep='last')
        print(f"Length of dataframe after dropping duplicates: {len(df)}")

        # Обрабатываем колонки нового файла
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='%d.%m.%y %H:%M:%S', errors='coerce')
        df = df.sort_values(by=['vm', 'metric', 'timestamp'], ascending=[True, True, True])

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

    # 1. Готовим данные значений метрик выгруженные по 20 серверам за период: с 25-11-2025 по 01-12-2025 (включительно)
    # Папка с данными data/source/temp/ собранный датафрейм сохраняется в файл data/processed/temp.xlsx
    #df = data.process_temp(folder_path='../data/source/temp',
    #                       out_file='../data/processed/25-11-2025_01-12-2025.xlsx')

    # 2. Готовим данные значений метрик выгруженные по всем серверам и сферам за период: с 04-12-2025 по 07-12-2025 (включительно)
    # Исходник находится в файле data/source/data.csv и сохраняется в файл data/processed/data.xlsx
    df = data.process_data(in_file='../data/source/data.csv',
                           out_file='../data/processed/data.xlsx')

    # 3. Далее создаем сводную таблицу по этим серверам и метрикам
    # df_wide = data.pivot_metrics()

    # 3. Готовим данные по

