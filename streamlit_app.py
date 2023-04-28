# -*- coding: utf-8 -*-
# !python -m pip --trusted-host=pypi.org --trusted-host=files.pythonhosted.org install --default-timeout=100 --upgrade streamlit-folium
# !python -m pip --trusted-host=pypi.org --trusted-host=files.pythonhosted.org install --default-timeout=100 --upgrade streamlit
# !python -m pip --trusted-host=pypi.org --trusted-host=files.pythonhosted.org install --default-timeout=100 --upgrade folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium
import folium
from folium import plugins
from maplegend import *

def color_producer(point, p_region, hex_palette):
    #составляет ТОП-12 + ПРОЧИЕ по заданному региону
    region = points_rating(p_region)
    
    #берём название всех компаний
    companies = region.name.tolist()
    #удаляем ПРОЧИЕ
    companies.pop()
    
    #автоматически присваиваем компаниям цвета из палитры
    comp_n_colors = {}
    x = 0
    for i in companies:
        comp_n_colors[hex_palette[x]] = [i]
        x += 1    

    
    #для легенды - запоминаем назначенные названия компаний с количеством точек
    global labels
    labels = [region.labels.tolist()[i] for i in range(0, len(comp_n_colors)+1)]
    
    #для легенды - запоминаем назначенные цвета    
    global colors
    colors = list(comp_n_colors.keys())
    colors.append('grey')
    
    
    #используем цвета для раскраски точек по названию компании
    for k, v in comp_n_colors.items():
        if any(company in point for company in v):
            return k
    return 'grey'


#загружаем файл с координатами
file = st.file_uploader('Загрузите файл Excel с координатами точек:', type = ['.xlsx', '.xlsm', 'xls'])
#образец файла для пользователя
st.write("Пример исходной таблицы:")
st.image("https://i.ibb.co/c8DJ9ZP/f3580096-358a-4ab2-b07b-d41895789bd9.jpg")

regions_list = []
if file != None:
    points = pd.read_excel(file)
    points.rename(columns = {'Наименование':'name',
                             'Адрес':'address',
                             'Широта': 'lat',
                             'Долгота':'lon',
                             'Город':'city',
                             'Регион':'SubRegion'}, inplace = True)
    points = points[~points.lat.isna()]
    #выбор интересующих регионов или все на одной карте
    values = ['Все регионы на одной карте']
    values.extend(points.SubRegion.drop_duplicates().tolist())
    regions_list = st.multiselect('Выберите регион', values)

    #если выбраны конкретные регионы - отбираем только подходящие точки
    if regions_list !=  ["Все регионы на одной карте"]:
        points = points[points.SubRegion.isin(regions_list)]
        
    #показываем выбранные точки
    st.dataframe(points, width=725)


col01, col02 = st.columns(2)
with col01:
    point_size = st.slider('Размер точек', 50, 200, 90)
with col02:
    #если пользователь хочет отображать города на карте
    city_on = st.checkbox('Отображать города на карте')

#настройка легенды
st.write("Настройка легенды:")
#создаем таблицу 3х4 для цветов
col1, col2, col3, col4 = st.columns(4)
with col1:
   hex1 = st.color_picker('Цвет 1', '#FF1100', key = 1)
   hex5 = st.color_picker('Цвет 5', '#006fff', key = 2)
   hex9 = st.color_picker('Цвет 9', '#ff9000', key = 3)
with col2:
   hex2 = st.color_picker('Цвет 2', '#64e600', key = 4)
   hex6 = st.color_picker('Цвет 6', '#e600d7', key = 5)
   hex10 = st.color_picker('Цвет 10', '#00d7e6', key = 6) 
with col3:
   hex3 = st.color_picker('Цвет 3', '#d7e600', key = 7)
   hex7 = st.color_picker('Цвет 7', '#00c0ff', key = 8)
   hex11 = st.color_picker('Цвет 11', '#9383c9', key = 9)
with col4:
   hex4 = st.color_picker('Цвет 4', '#670A02', key = 10)
   hex8 = st.color_picker('Цвет 8', '#1E0267', key = 11)
   hex12 = st.color_picker('Цвет 12', '#106702', key = 12)
#сохраняем выбранные цвета
hex_palette = [hex1,hex2,hex3,hex4,hex5,hex6,hex7,hex8,hex9,hex10,hex11,hex12]


#если пользователь отмечает города и выбрал какой-либо регион
if city_on and regions_list != []:
    #подгружаем базу городов
    city_db = pd.read_csv(r'https://raw.githubusercontent.com/Evgeny-Larin/OnlineMaps_Folium/main/db/cities_db.csv',usecols=['CityName', 'SubRegion', 'Latitude', 'Longitude', 'Population'], encoding='windows-1251', sep = ';')
    #из базы берём только необходимые города
    city_db = city_db[city_db['CityName'].isin(points.city.drop_duplicates().tolist())]


#если выбрано "Все регионы на одной карте" - строим одну карту
if regions_list ==  ["Все регионы на одной карте"]:

    #создаем карту
    russia_map = folium.Map(location = [points.lat.median(), points.lon.median()], #начальная позиция камеры
                            zoom_start = 7, #начальный зум камеры
                            tiles = 'cartodbpositron') #стиль карты
    
    #добавляем плагины
    #полноэкранный режим
    plugins.Fullscreen(
    position="bottomleft",
    force_separate_button=True).add_to(russia_map)
    #поиск
    plugins.Geocoder(collapsed=True, position='topleft').add_to(russia_map)
    #миникарта
    minimap = plugins.MiniMap()
    russia_map.add_child(minimap)
    
    #если отмечаем города на карте - отмечаем их на карте    
    if city_on:
        city_db.apply(lambda row:folium.Circle(location=[row["Latitude"], row["Longitude"]], #координаты города
                                            radius=(row["Population"]/55 if row["Population"]/50>6000 else 6000), #радиус окружности
                                            tooltip=row['CityName'], #всплывающая подсказка
                                            fill=True, #настройка заполнения цветом
                                            weight=1,  #настройка прозрачности и т.д.
                                            fill_opacity=0.02).add_to(russia_map), axis=1)

    #из points получаем точки и отмечаем их на карте
    points.apply(lambda row:folium.Circle(location=[row["lat"], row["lon"]], 
                                         radius=point_size,
                                         popup=repr(row['address']), #нажатие на точку (пока отключено, почему-то не открывается файл Томской области)
                                         tooltip=row['name'], 
                                         fill = True, 
                                         weight=0.5, 
                                         color = 'black', 
                                         weight_color = 'black', 
                                         fill_opacity=1, 
                                         fill_color=color_producer(row['name'], points, hex_palette)).add_to(russia_map), axis=1)

    #добавляем легенду на карту
    russia_map = add_categorical_legend(russia_map, '',
                                        colors = colors,
                                        labels = labels)
    
    #преобразовываем объект карты (russia_map) в HTML-строку
    map_html = russia_map.get_root().render()
    
    #создаем кнопку для загрузки файла 
    file_name = "Общая карта.html"
    button = st.download_button(label=f"Сохранить карту: {file_name}", data=map_html, file_name=file_name)
    
    #выводим карту на страницy
    st_folium(russia_map, width = 725)    

#если выбраны конкретные регионы - строим карту для каждого региона
else:
    for i in regions_list:
        points_region = points[(points['SubRegion'] == i)]
    
        #создаем карту
        russia_map = folium.Map(location = [points_region.lat.median(), points_region.lon.median()], #начальная позиция камеры
                                zoom_start = 7, #начальный зум камеры
                                tiles = 'cartodbpositron') #стиль карты
        
        #добавляем плагины
        #полноэкранный режим
        plugins.Fullscreen(
        position="bottomleft",
        force_separate_button=True).add_to(russia_map)
        #поиск
        plugins.Geocoder(collapsed=True, position='topleft').add_to(russia_map)
        #миникарта
        minimap = plugins.MiniMap()
        russia_map.add_child(minimap)
        
        #если отмечаем города на карте - отмечаем их на карте
        if city_on:
            city_db.query(f'SubRegion == "{i}"').apply(lambda row:folium.Circle(location=[row["Latitude"], row["Longitude"]], #координаты города
                                                radius=(row["Population"]/60 if row["Population"]/50>6000 else 6000), #радиус окружности
                                                tooltip=row['CityName'], #всплывающая подсказка
                                                fill=True, #настройка заполнения цветом
                                                weight=1,  #настройка прозрачности и т.д.
                                                fill_opacity=0.02).add_to(russia_map), axis=1)
    
        #из points получаем точки и отмечаем их на карте
        points_region.apply(lambda row:folium.Circle(location=[row["lat"], row["lon"]], 
                                             radius=point_size,
                                             popup=repr(row['address']), #нажатие на точку (пока отключено, почему-то не открывается файл Томской области)
                                             tooltip=row['name'], 
                                             fill = True, 
                                             weight=0.5, 
                                             color = 'black', 
                                             weight_color = 'black', 
                                             fill_opacity=1, 
                                             fill_color=color_producer(row['name'], points_region, hex_palette)).add_to(russia_map), axis=1)
    
        #добавляем легенду на карту
        russia_map = add_categorical_legend(russia_map, '',
                                            colors = colors,
                                            labels = labels)
        
        #преобразовываем объект карты (russia_map) в HTML-строку
        map_html = russia_map.get_root().render()
        
        #создаем кнопку для загрузки файла 
        file_name = f"{i} - карта.html"
        button = st.download_button(label=f"Сохранить карту: {i}", data=map_html, file_name=file_name)
        
        #выводим карту на страницy
        st_folium(russia_map, width = 725)