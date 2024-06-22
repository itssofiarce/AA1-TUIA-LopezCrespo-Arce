#!/usr/bin/env python
# coding: utf-8

# In[4]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import sqrt

# Pipeline
from sklearn.base import BaseEstimator, TransformerMixin
# Estandarización y modelado
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
# Division de los datos
from sklearn.model_selection import train_test_split
# Normalización
# Regresiones
from sklearn.linear_model import LogisticRegression
# ML metricas
from sklearn.metrics import accuracy_score
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score


# In[5]:


df = pd.read_csv('weatherAUS.csv',usecols=range(1,25))


# pipeline que limpia datos

# In[6]:


class ColDropper(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.drop(["Unnamed: 0", "Date"], axis=1)


class LocDropper(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        aus_loc = [
            " Adelaide",
            "Canberra",
            "Cobar",
            "Dartmoor",
            "Melbourne",
            "MelbourneAirport",
            "MountGambier",
            "Sydney",
            "SydneyAirport",
        ]
        return X[X["Location"].isin(aus_loc)]


class CatFiller(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X["WindGustDir"] = X.groupby("Location")["WindGustDir"].transform(
            lambda x: x.fillna(x.mode()[0])
        )
        X["WindDir9am"] = X.groupby("Location")["WindDir9am"].transform(
            lambda x: x.fillna(x.mode()[0])
        )
        X["WindDir3pm"] = X.groupby("Location")["WindDir3pm"].transform(
            lambda x: x.fillna(x.mode()[0])
        )

        return X


class NumFiller(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        remanining_vnul_columns = X.columns[X.isna().any()].tolist()
        for col in remanining_vnul_columns:
            X[col] = X[col].fillna(X[col].mean())

        return X


# https://www.mdpi.com/2078-2489/13/4/163 Como las variables de la dirección de los vientos pueden tener hasta 16 direcciones diferentes, para convertirlos a variables numéricas, se tiene encuenta una distribución circular. Por eso, cada una de las variables se dividió en dos: Una con el seno y otra con el coseno del angulo
class CoordRecat(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        coord = {
            "N": 0,
            "NNE": 22.5,
            "NE": 45,
            "ENE": 67.5,
            "E": 90,
            "ESE": 112.5,
            "SE": 135,
            "SSE": 157.5,
            "S": 180,
            "SSW": 202.5,
            "SW": 225,
            "WSW": 247.5,
            "W": 270,
            "WNW": 292.5,
            "NW": 315,
            "NNW": 337.5,
        }

        # Aplicar la recategorización
        for col in ["WindGustDir", "WindDir9am", "WindDir3pm"]:
            X[col] = X[col].map(coord)
            X[f"{col}_rad"] = np.deg2rad(X[col])
            X[f"{col}_sin"] = np.sin(X[f"{col}_rad"]).round(5)
            X[f"{col}_cos"] = np.cos(X[f"{col}_rad"]).round(5)

        # Eliminar columnas originales y columnas radianes
        columns_to_drop = [
            f"{col}_rad" for col in ["WindGustDir", "WindDir9am", "WindDir3pm"]
        ] + ["WindGustDir", "WindDir9am", "WindDir3pm"]
        X = X.drop(columns=columns_to_drop, axis=1)

        return X


class LocEncoder(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        dummies = pd.get_dummies(X["Location"], dtype=int)
        X = pd.concat([X, dummies], axis=1)
        X.drop("Location", axis=1, inplace=True)

        return X


class ResetIndex(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.reset_index(drop=True)


class Standarizer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # Exclusión de variables booleanas y RainfallTmorrow porque no serán estandarizaradas
        exc_c = ["RainToday", "RainTomorrow", "RainfallTomorrow"]

        # Estandarización
        df_sub = X[[col for col in X.columns if col not in exc_c]]
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_sub)

        X_scaled = pd.DataFrame(X_scaled, columns=df_sub.columns)
        for col in exc_c:
            X_scaled[f"{col}"] = X[col]

        # Nuevo DataFrame estandarizado con los nombres de las columnas originales
        return X_scaled


class OutliersTreater(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        cols_with_ouliers = [
            "MinTemp",
            "MaxTemp",
            "Rainfall",
            "Evaporation",
            "Sunshine",
            "WindGustSpeed",
            "WindSpeed9am",
            "WindSpeed3pm",
            "Humidity9am",
            "Humidity3pm",
            "Pressure9am",
            "Pressure3pm",
            "Cloud9am",
            "Cloud3pm",
            "Temp9am",
            "Temp3pm",
        ]

        for col in cols_with_ouliers:
            IQR = X[col].quantile(0.75) - X[col].quantile(0.25)
            lower_bridge = X[col].quantile(0.25) - (IQR * 1.5)
            upper_bridge = X[col].quantile(0.75) + (IQR * 1.5)

            X.loc[X[col] >= round(upper_bridge, 2), col] = round(upper_bridge, 2)
            X.loc[X[col] <= round(lower_bridge, 2), col] = round(lower_bridge, 2)

        return X


class ColDropper(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.drop(["Date"], axis=1)


class LocDropper(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        costa_este = [
            " Adelaide",
            "Canberra",
            "Cobar",
            "Dartmoor",
            "Melbourne",
            "MelbourneAirport",
            "MountGambier",
            "Sydney",
            "SydneyAirport",
        ]
        X.loc[X["Location"].isin(costa_este), "Location"] = "costa_este"
        return X[X["Location"] == "costa_este"]


class CatFiller(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X["WindGustDir"] = X.groupby("Location")["WindGustDir"].transform(
            lambda x: x.fillna(x.mode()[0])
        )
        X["WindDir9am"] = X.groupby("Location")["WindDir9am"].transform(
            lambda x: x.fillna(x.mode()[0])
        )
        X["WindDir3pm"] = X.groupby("Location")["WindDir3pm"].transform(
            lambda x: x.fillna(x.mode()[0])
        )

        return X


class NumFiller(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        remanining_vnul_columns = X.columns[X.isna().any()].tolist()
        for col in remanining_vnul_columns:
            X[col] = X[col].fillna(X[col].mean())

        return X


# https://www.mdpi.com/2078-2489/13/4/163 Como las variables de la dirección de los vientos pueden tener hasta 16 direcciones diferentes, para convertirlos a variables numéricas, se tiene encuenta una distribución circular. Por eso, cada una de las variables se dividió en dos: Una con el seno y otra con el coseno del angulo
class CoordRecat(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        coord = {
            "N": 0,
            "NNE": 22.5,
            "NE": 45,
            "ENE": 67.5,
            "E": 90,
            "ESE": 112.5,
            "SE": 135,
            "SSE": 157.5,
            "S": 180,
            "SSW": 202.5,
            "SW": 225,
            "WSW": 247.5,
            "W": 270,
            "WNW": 292.5,
            "NW": 315,
            "NNW": 337.5,
        }

        # Aplicar la recategorización
        for col in ["WindGustDir", "WindDir9am", "WindDir3pm"]:
            X[col] = X[col].map(coord)
            X[f"{col}_rad"] = np.deg2rad(X[col])
            X[f"{col}_sin"] = np.sin(X[f"{col}_rad"]).round(5)
            X[f"{col}_cos"] = np.cos(X[f"{col}_rad"]).round(5)

        # Eliminar columnas originales y columnas radianes
        columns_to_drop = [
            f"{col}_rad" for col in ["WindGustDir", "WindDir9am", "WindDir3pm"]
        ] + ["WindGustDir", "WindDir9am", "WindDir3pm"]
        X = X.drop(columns=columns_to_drop, axis=1)

        return X


class LocEncoder(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        dummies = pd.get_dummies(X["Location"], dtype=int)
        X = pd.concat([X, dummies], axis=1)
        X.drop("Location", axis=1, inplace=True)

        return X


class ResetIndex(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X.reset_index(drop=True)


class BoolYNDropperEncoder(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X.dropna(subset=["RainToday"], inplace=True)
        X["RainTomorrow"] = X["RainTomorrow"].map({"No": 0, "Yes": 1}).astype(float)
        X["RainToday"] = X["RainToday"].map({"No": 0, "Yes": 1}).astype(float)

        return X


class Standarizer(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        # Exclusión de variables booleanas y RainfallTmorrow porque no serán estandarizaradas
        exc_c = ["RainToday", "RainTomorrow"]

        # Estandarización
        df_sub = X[[col for col in X.columns if col not in exc_c]]
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(df_sub)

        X_scaled = pd.DataFrame(X_scaled, columns=df_sub.columns)
        for col in exc_c:
            X_scaled[f"{col}"] = X[col]

        # Nuevo DataFrame estandarizado con los nombres de las columnas originales
        return X_scaled


class OutliersTreater(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        cols_with_ouliers = [
            "MinTemp",
            "MaxTemp",
            "Rainfall",
            "Evaporation",
            "Sunshine",
            "WindGustSpeed",
            "WindSpeed9am",
            "WindSpeed3pm",
            "Humidity9am",
            "Humidity3pm",
            "Pressure9am",
            "Pressure3pm",
            "Cloud9am",
            "Cloud3pm",
            "Temp9am",
            "Temp3pm",
        ]

        for col in cols_with_ouliers:
            IQR = X[col].quantile(0.75) - X[col].quantile(0.25)
            lower_bridge = X[col].quantile(0.25) - (IQR * 1.5)
            upper_bridge = X[col].quantile(0.75) + (IQR * 1.5)

            X.loc[X[col] >= round(upper_bridge, 2), col] = round(upper_bridge, 2)
            X.loc[X[col] <= round(lower_bridge, 2), col] = round(lower_bridge, 2)

        return X


class RLValDropper(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X.dropna(subset=["RainTomorrow"], inplace=True)
        X.dropna(subset=["RainfallTomorrow"], inplace=True)
        return X

# DESCARTAR VARIABLES NO NUMERICAS Y ACOMODAR EL DATASET PARA ML OPS
# SOLAMENTE ML-OPS
cols = ['costa_este','WindGustDir_sin',	'WindGustDir_cos','WindDir9am_sin',	'WindDir9am_cos','WindDir3pm_sin','WindDir3pm_cos']
class DescartarNoUsarMlOPS(BaseEstimator, TransformerMixin):
    def fit(self, X,y=None):
        return self
    
    def transform(self,X):
        X = X.drop(cols, axis=1)
        return X


## Pipeline

# * Descartar Unnamed y Date porque son features que no vamos a utilizar: **ColDropper** (Ademas droppear RainfallTomorrow para prevenir la fuga de datos)
# * Descartar todas las location que no son necesarias: **LocDropper**
# * Dropear nulos y Label Encoding para las variables yes/no: **BoolYNDropperEncoder**
# * Imputar valores nulos en variables categoricas con la moda: **CatFiller**
# * Imputar valores nulos en variables numericas con la media:  **NumFiller**
# * One Hot Encoding para las location: **LocEncoder**
# * Encoding en sin y cos para WinDir: **CoordRecat**
# * Estandarizar valores: **Standarizer**

preprocessor = Pipeline(
    [
        ("drop_null_val_rl", RLValDropper()),
        ("drop_not_needed_features", ColDropper()),
        ("drop_nor_needed_locations", LocDropper()),
        ("yes_no_dropper_encoder", BoolYNDropperEncoder()),
        ("fill_null_cat", CatFiller()),
        ("fill_num_cat", NumFiller()),
        ("encode_loc", LocEncoder()),
        ("encode_wind_dir", CoordRecat()),
        ("reset_index", ResetIndex()),
        ("treat_outliers", OutliersTreater()),
        ("standariza_values", Standarizer()),
        ("Preparar_MLOPS", DescartarNoUsarMlOPS())
    ]
)


# split

# In[7]:


# Separación de variables explicativas y variables objetivo
X = df.drop(['RainTomorrow', ], axis=1).copy()
y = df[['RainTomorrow']].copy()

# Spliteo mi dataset en train-test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
X_train.shape, X_test.shape, y_train.shape, y_test.shape


# In[8]:


# Creo un Dataframe de TRAIN
df_train = pd.DataFrame(X_train, columns=X.columns)
df_train['RainTomorrow'] = y['RainTomorrow']


# In[9]:


# Creo un Dataframe de TEST
df_test = pd.DataFrame(X_test, columns=X.columns)
df_test['RainTomorrow'] = y['RainTomorrow']


# In[10]:


#Preproceso mi df de test y mi df de train
df_train = preprocessor.fit_transform(df_train)
df_test = preprocessor.fit_transform(df_test)


# In[11]:


# def clean_train(traindf):
#     df_train = preprocessor.fit_transform(traindf)

#     return df_train


# In[12]:


# def clean_test(testdf):
#     df_test = preprocessor.transform(testdf)

#     return df_test


# In[13]:


# df_train = clean_train(df_train)


# In[14]:


# df_test = clean_train(df_test)


# In[15]:


X_train_clasificacion = df_train.drop(['RainTomorrow', 'RainfallTomorrow'], axis=1).copy()
y_train_clasificacion = df_train['RainTomorrow'].copy()

X_test_clasificacion = df_test.drop(['RainTomorrow','RainfallTomorrow'], axis=1).copy()
y_test_clasificacion = df_test['RainTomorrow'].copy()


# In[16]:


X_train_regresion = df_train.drop(['RainTomorrow','RainfallTomorrow'], axis=1).copy()
y_train_regresion = df_train['RainfallTomorrow'].copy()

X_test_regresion = df_test.drop(['RainTomorrow','RainfallTomorrow'], axis=1).copy()
y_test_regresion = df_test['RainfallTomorrow'].copy()


# In[17]:


X_test_clasificacion


# In[18]:


class RegLogistica(BaseEstimator, TransformerMixin):
    def __init__(self):
        self.parametros = {
            "C": 10,
            "class_weight": "balanced",
            "max_iter": 500,
            "solver": "newton-cg",
        }
        self.pipeline = None
        self.model = None
        self.y_pred_clasificacion = None

    def fit(self, X, y):
        if self.parametros:
            self.model = LogisticRegression(**self.parametros)
            self.model.fit(X_train_clasificacion, y_train_clasificacion)
        else:
            raise ValueError("Se necesita pasarle parametros al modelo")

        return self

    def predict(self, X):
        if self.model:
            y_pred_clasificacion = self.model.predict(X_test_clasificacion)
            return y_pred_clasificacion
        else:
            raise ValueError("hubo un error entrenando el modelo")

    def metrics(self, y_test_clasificacion):
        if y_test_clasificacion is None:
            raise ValueError("Se necesita el set de prueba")
        
        if self.y_pred_clasificacion is None:
            raise ValueError("Se necesita predecir")

        accuracy = accuracy_score(y_test_clasificacion, self.y_pred_clasificacion)
        precision = precision_score(y_test_clasificacion, self.y_pred_clasificacion)
        recall = recall_score(y_test_clasificacion, self.y_pred_clasificacion)
        f1 = f1_score(y_test_clasificacion, self.y_pred_clasificacion)

        metrics = {
            "Accuracy": accuracy,
            "Precision": precision,
            "Recall": recall,
            "F1 Score": f1,
        }

        return metrics


# In[19]:


reg_logistica = RegLogistica()

# Crear el pipeline completo
classification_pipeline = Pipeline([

    ('classification_pipeline', reg_logistica)
])

classification_pipeline


# In[20]:


# Entrenar el pipeline con los datos de entrenamiento
classification_pipeline.fit(X_train, y_train)

# Hacer predicciones en los datos de prueba
y_pred_class = classification_pipeline.predict(X_train_clasificacion)



# In[21]:


from sklearn.metrics import recall_score, accuracy_score, precision_score
print(f"Recall: {recall_score(y_test_clasificacion, y_pred_class)}")
print(f"Precision: {precision_score(y_test_clasificacion, y_pred_class)}")
print(f"Accuracy: {accuracy_score(y_test_clasificacion, y_pred_class)}")


# In[22]:


import joblib


# In[23]:


joblib.dump(classification_pipeline, 'joblib/rain_pred_clasificacion.joblib')

