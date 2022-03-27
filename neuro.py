# import mysql.connector as mc
# import numpy as np
# import tensorflow as tf
# from PyQt5.QtWidgets import QMessageBox
# from keras import models
# from keras.applications.densenet import layers
# from tensorflow import keras
# import matplotlib.pyplot as plt
# import sklearn as sk
# from sklearn import preprocessing
#
# outputData = list()
# inputData = list()
#
#
# def getDataFromDB():
# 	try:
# 		query = (
# 			"SELECT weight_chugun, temperature_chugun, si_weight_percent, mn_weight_percent, c_weight_percent, p_weight_percent, "
# 			"s_weiht_percent, weight_lom, si_lom_weight_percent, mn_lom_weight_percent, c_lom_weight_percent, p_lom_weight_percent,"
# 			" s_lom_weight_percent, flus_1, flus_2, flus_3, flus_4, mixer_slag, v_d, t_d FROM input_params;")
#
# 		DB = mc.connect(
# 			host="localhost",
# 			user="root",
# 			password="root",
# 			database="regimdata"
# 		)
# 		result = ""
# 		mycursor = DB.cursor()
# 		mycursor.execute(query)
# 		inputData = mycursor.fetchall()
# 		mycursor.close()
# 		query = (
# 			"SELECT metal_weight, metal_temperature, si_metal_weight_percent, mn_metal_weight_percent, c_metal_weight_percent, "
# 			"p_metal_weight_percent, s_metal_weight_percent, metal_output_time, slag_weight, cao_slag_weight_percent, "
# 			"sio2_slag_weight_percent, mgo_slag_weight_percent, feo_slag_weight_percent, al2o3_slag_weight_percent, "
# 			"mno_slag_weight_percent, p2o5_slag_weight_percent, s_slag_weight_percent FROM output_params;")
#
# 		mycursor = DB.cursor()
# 		mycursor.execute(query)
# 		outputData = mycursor.fetchall()
#
# 		trainData = np.array(inputData)
# 		trainData = trainData.transpose()
# 		normsin = list()
# 		normsout = list()
#
# 		for i in range(len(trainData)):
# 			normsin.append(list())
# 			trainData[i], normsin[i] = preprocessing.normalize([trainData[i]], norm='l2', return_norm=True)
#
# 		normsin = np.array(normsin)
# 		trainData = trainData.transpose()
# 		trainData.reshape(len(trainData), 20)
#
# 		outData = np.array(outputData)
# 		outData = outData.transpose()
#
# 		for i in range(len(outData)):
# 			normsout.append(list())
# 			outData[i], normsout[i] = preprocessing.normalize([outData[i]], norm='l2', return_norm=True)
# 		normsout = np.array(normsout)
# 		outData = outData.transpose()
# 		outData.reshape(len(outData), 17)
#
# 		model = models.Sequential()
# 		model.add(layers.Dense(128, activation='relu', input_shape=(trainData.shape[1],)))
# 		model.add(layers.Dense(128, activation='relu'))
# 		model.add(layers.Dense(17))
# 		model.compile(optimizer='rmsprop', loss='mse', metrics=['mae'])
#
# 		model.summary()
# 		model.fit(trainData, outData, epochs=100, batch_size=16, verbose=0)
#
# 	except Exception as err:
# 		msg = QMessageBox()
# 		msg.setIcon(QMessageBox.Critical)
# 		msg.setWindowTitle("Ошибка")
# 		msg.setText("Внимание")
# 		msg.setInformativeText("Проверьте введенные данные! {0}".format(err))
# 		# msg.setInformativeText("Error: {0}".format(err))
# 		msg.exec_()
#
# 	finally:
# 		mycursor.close()
# 		DB.close()
#
#
#
#
#
# def build_model():
# 	model = models.Sequential()
# 	model.add(layers.Dense(128,activation='relu', input_shape=(inputData.shape[1],)))
# 	model.add(layers.Dense(128, activation='relu'))
# 	model.add(layers.Dense(17))
# 	model.compile(optimizer='rmsprop', loss='mse', metrics=['mae'])
# 	return model
#
#
# model = build_model()
# model.summary()
#
# model=build_model()
# model.fit(inputData, outputData, epochs= 100, batch_size=16, verbose=0)
