import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
import numpy as np

# Escolher arquivo
csv_path = '/home/oranor-gnb/test/oranor-xapp-experimenting/Model_test/xgboost_13-03-2025_13-39-50_6-20250331-135327/xgboost_13-03-2025_13-39-50_6_metrics_31032025-135331.csv'
# Escolher entre colunas coletadas ou processadas
columns_to_plot = ['PRB Available (UL)', 'PRB Total (UL)', 'MCS (UL)', 'SNR']
#columns_to_plot = ['Airtime', 'SNR' ] #, 'MCS']


# Escolher o tamanho da fonte
font_size = 17
plt.rcParams.update({'font.size': font_size})

df = pd.read_csv(csv_path)

# Selecionar colunas e renomear colunas coletadas ou processadas 
df = df.iloc[:, 3:7]
df = df.rename(columns={
    'RRU.PrbAvailUl': 'PRB Available (UL)',
    'RRU.PrbTotUl': 'PRB Total (UL)',
    'McsUl': 'MCS (UL)',
    'SNR': 'SNR'
})

# df = df.iloc[:, 8:11]
# df = df.rename(columns={
#     'Airtime_Norm': 'Airtime',
#     'SNR_Norm': 'SNR',
# #    'Mcs_Norm': 'MCS'
# }) 

#Normalizar
scaler = StandardScaler()
df[columns_to_plot] = scaler.fit_transform(df[columns_to_plot])

plt.figure(figsize=(12, 6))
for col in columns_to_plot:
    plt.plot(df[col], label=col)

#plt.title('xApp Metrics collection') # Ajustar título e labels dos eixos
plt.xlabel('Time [s]')
plt.ylabel('Features')
plt.xticks(fontsize=font_size)
plt.yticks(fontsize=font_size)
plt.xticks(np.arange(0, 560, 60)) # Ajustar limites para os do experimento
plt.xlim(0,560)
plt.legend(fontsize=14,loc='upper left')

plt.grid(True)
plt.tight_layout()

plt.savefig('xapp_metrics_no_buffer.png') # Ajustar nome do arquivo com o gráfico

