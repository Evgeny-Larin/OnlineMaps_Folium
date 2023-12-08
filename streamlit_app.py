import streamlit as st
from streamlit_folium import st_folium
from map_components import *
import sqlite3
import urllib.request

# содержимое страницы по ширине (по умолчанию по центру)
st.set_page_config(page_title = 'Map Generator', page_icon = '🗺️', layout="wide")

# загружаем файл с координатами
file = st.file_uploader('Загрузите файл Excel с координатами точек:', type = ['.xlsx', '.xlsm', '.xls', '.xlsb'])

# образец файла для пользователя
with st.expander("Пример исходной таблицы"):
    txt = st.write('''Скачайте и заполните шаблон исходной таблицы собственными данными. Столбцы "Широта" и "Долгота" являются обязательными.''')
    redirect_button(r"https://github.com/Evgeny-Larin/online_maps_folium/raw/main/source/example.xlsx","Скачать шаблон")

regions_list = []
if file != None:
    points = pd.read_excel(file)
    points.rename(columns = {'Наименование':'name',
                             'Адрес':'address',
                             'Широта': 'lat',
                             'Долгота':'lon',
                             'Город':'city',
                             'Регион':'SubRegion'}, inplace = True)
    
    points['name'].fillna('Имя не указано', inplace = True)        
    points['address'].fillna('Адрес не указан', inplace = True) 
    points['city'].fillna('Город не указан', inplace = True) 
    points['SubRegion'].fillna('Регион не указан', inplace = True)
    
    points = points[(~points.lat.isna())&(~points.lon.isna())]
    # выбор интересующих регионов или все на одной карте
    values = ['Все регионы на одной карте']
    values.extend(points.SubRegion.drop_duplicates().tolist())
    regions_list = st.multiselect('Выберите регион', values)

    # если выбраны конкретные регионы - отбираем только подходящие точки
    if "Все регионы на одной карте" not in regions_list:
        points = points[points.SubRegion.isin(regions_list)]


col01, col02 = st.columns(2)

# задаем настройки карты
with st.sidebar:
    st.write("Настройка карты:")
    mapstyle = st.radio(
                "Стиль:",
                ('Стандартная цветная', 'Стандартная приглушённая', 'ЖД пути и станции', 'ЖД пути и станции 2'))

    city_on = st.checkbox('Отображать города на карте')
    minimap_on = st.checkbox('Отображать мини-карту')
    clasters_on = st.checkbox('Группировать точки при изменении масштаба')

    point_size = st.slider('Размер точек', 10, 200, 90)
    zoom = st.slider('Исходный масштаб карты', 1, 15, 7)

    # настройка легенды
    st.write("Настройка легенды:")
    # создаем таблицу 3х4 для цветов
    col1, col2, col3, col4 = st.columns(4)
    with col1:
       hex1 = st.color_picker('Цвет 1', '#980387', key = 1)
       hex5 = st.color_picker('Цвет 5', '#7f9c21', key = 2)
       hex9 = st.color_picker('Цвет 9', '#f12121', key = 3)
    with col2:
       hex2 = st.color_picker('Цвет 2', '#ff9000', key = 4)
       hex6 = st.color_picker('Цвет 6', '#441066', key = 5)
       hex10 = st.color_picker('Цвет 10', '#00d7e6', key = 6) 
    with col3:
       hex3 = st.color_picker('Цвет 3', '#f70068', key = 7)
       hex7 = st.color_picker('Цвет 7', '#f15821', key = 8)
       hex11 = st.color_picker('Цвет 11', '#E600D7', key = 9)
    with col4:
       hex4 = st.color_picker('Цвет 4', '#2970e2', key = 10)
       hex8 = st.color_picker('Цвет 8', '#64E600', key = 11)
       hex12 = st.color_picker('Цвет 12', '#9383C9', key = 12)
       

       
# сохраняем выбранные цвета
hex_palette = [hex1, hex2, hex3, hex4, hex5, hex6, hex7, hex8, hex9, hex10, hex11, hex12]


# если пользователь отмечает города и выбрал какой-либо регион
if city_on and regions_list != []:
    # подключаемся к базе городов
    urllib.request.urlretrieve(r'https://github.com/Evgeny-Larin/online_maps_folium/raw/main/db/cities_db.db', 'cities_db.db')
    conn = sqlite3.connect('cities_db.db')
    
    # из базы берём только необходимые города
    city_list = points.city.unique()
    city_list = ', '.join(f"'{x}'" for x in city_list)
    city_db = pd.read_sql(con=conn, sql = f'SELECT * FROM cities WHERE CityName IN ({city_list})')


# если выбрано "Все регионы на одной карте" - строим одну карту
if regions_list ==  ["Все регионы на одной карте"]:
           
    # создаем карту
    russia_map = map_creator(points, mapstyle, minimap_on, zoom)
    
    # если отмечаем города на карте - отмечаем их на карте    
    if city_on:
        city_creator(city_db, russia_map)

    # отмечаем точки на карте    
    points_creator(points, russia_map, hex_palette, point_size, clasters_on)
    
    # добавляем пользовательскую подпись (атрибуцию) в правой нижней части карты
    add_atr(russia_map)
    
    # преобразовываем объект карты (russia_map) в HTML-строку
    map_html = russia_map.get_root().render()
    
    # создаем кнопку для загрузки файла 
    file_name = "Общая карта.html"
    button = st.download_button(label=f"Сохранить карту: {file_name}", data=map_html, file_name=file_name)
    
    # выводим предпросмотр карты на страницy
    st_folium(russia_map,
              height=500,
              width=1200)

# если выбраны конкретные регионы - строим карту для каждого региона
else:
    for i in regions_list:
        # если пользователь выбрал конкретные регионы И опцию "Все регионы на одной карте"
        # для "Все регионы на одной карте" - берем основной df
        if i ==  "Все регионы на одной карте":
            points_region = points.copy()
        # для регионов - выбираем из основного df нужные регионы
        else:
            points_region = points[(points['SubRegion'] == i)]            
    
        # создаем карту
        russia_map = map_creator(points_region, mapstyle, minimap_on, zoom)

        # если отмечаем города на карте - отмечаем их на карте
        if city_on:
            city_db = city_db.query(f'SubRegion == "{i}"')
            city_creator(city_db, russia_map)
        
        # отмечаем точки на карте
        points_creator(points_region, russia_map, hex_palette, point_size, clasters_on)
        
        # добавляем пользовательскую подпись (атрибуцию) в правой нижней части карты
        add_atr(russia_map)
        
        # преобразовываем объект карты (russia_map) в HTML-строку
        map_html = russia_map.get_root().render()
        
        # создаем кнопку для загрузки файла 
        file_name = f"{i} - карта.html"
        button = st.download_button(label=f"Сохранить карту: {i}", data=map_html, file_name=file_name, key = i)
        
        # выводим предпросмотр карты на страницy
        st_folium(russia_map,
                  height=500,
                  width=1200,
                  key = i)