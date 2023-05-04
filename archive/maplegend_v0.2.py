#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#легенда для folium
import folium
import pandas as pd

def add_categorical_legend(folium_map, title, colors, labels):
    if len(colors) != len(labels):
        raise ValueError("colors and labels must have the same length.")

    color_by_label = dict(zip(labels, colors))
    
    legend_categories = ""     
    for label, color in color_by_label.items():
        legend_categories += f"<li><span style='background:{color}'></span>{label}</li>"
        
    legend_html = f"""
    <div id='maplegend' class='maplegend'>
      <div class='legend-title'>{title}</div>
      <div class='legend-scale'>
        <ul class='legend-labels'>
        {legend_categories}
        </ul>
      </div>
    </div>
    """
    script = f"""
        <script type="text/javascript">
        var oneTimeExecution = (function() {{
                    var executed = false;
                    return function() {{
                        if (!executed) {{
                             var checkExist = setInterval(function() {{
                                       if ((document.getElementsByClassName('leaflet-top leaflet-right').length) || (!executed)) {{
                                          document.getElementsByClassName('leaflet-top leaflet-right')[0].style.display = "flex"
                                          document.getElementsByClassName('leaflet-top leaflet-right')[0].style.flexDirection = "column"
                                          document.getElementsByClassName('leaflet-top leaflet-right')[0].innerHTML += `{legend_html}`;
                                          clearInterval(checkExist);
                                          executed = true;
                                       }}
                                    }}, 100);
                        }}
                    }};
                }})();
        oneTimeExecution()
        </script>
      """
   

    css = """

    <style type='text/css'>
      .maplegend {
        z-index:9999;
        float:right;
        background-color: rgba(255, 255, 255, 1);
        border-radius: 5px;
        border: 2px solid #bbb;
        padding: 10px;
        font-size:12px;
        positon: relative;
      }
      .maplegend .legend-title {
        text-align: left;
        margin-bottom: 5px;
        font-weight: bold;
        font-size: 90%;
        }
      .maplegend .legend-scale ul {
        margin: 0;
        margin-bottom: 5px;
        padding: 0;
        float: left;
        list-style: none;
        }
      .maplegend .legend-scale ul li {
        font-size: 80%;
        list-style: none;
        margin-left: 0;
        line-height: 18px;
        margin-bottom: 2px;
        }
      .maplegend ul.legend-labels li span {
        display: block;
        float: left;
        height: 16px;
        width: 30px;
        margin-right: 5px;
        margin-left: 0;
        border: 0px solid #ccc;
        }
      .maplegend .legend-source {
        font-size: 80%;
        color: #777;
        clear: both;
        }
      .maplegend a {
        color: #777;
        }
    </style>
    """

    folium_map.get_root().header.add_child(folium.Element(script + css))

    return folium_map


#заменяет полное название компании на сокращенное
def replacer(x):
    #словарь замен
    replace_dict = {'ОБЩЕСТВО С ОГРАНИЧЕННОЙ ОТВЕТСТВЕННОСТЬЮ': 'ООО',
                    'ПУБЛИЧНОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО': 'ПАО',
                    'ОТКРЫТОЕ АКЦИОНЕРНОЕ ОБЩЕСТВО': 'ОАО',
                    'АКЦИОНЕРНОЕ ОБЩЕСТВО': 'АО'}
    for old, new in replace_dict.items():
        x = x.upper().replace(old, new)
    return x

#принимает df с точками внутри региона (например, p_kem)
def points_rating(x):
    #выделим ТОП-12 по количеству наиболее крупных сетей, остальные сохраним в Прочие
    #посчитаем количество точек в той или иной сети
    points_count = x.groupby('name', as_index = False)\
                    .agg({'lat':'count'})\
                    .sort_values('lat', ascending = False)

    #назначим ранги для каждой сети, где 1 - самая крупная
    points_count['rank'] = points_count['lat'].rank(method = 'first', ascending = False)

    #сохраним отдельно ТОП-12 сетей
    top12 = points_count[(points_count['rank']<=12)].drop(columns = ['rank'])
    
    #сохраним отдельно прочие
    other_points = points_count[(points_count['rank']>12)].drop(columns = ['name'])
    #создадим столбец "Прочие"
    other_points['name'] = 'ПРОЧИЕ'
    #найдём суммарное количество точек всех прочих сетей
    other_points = other_points.groupby('name', as_index = False)\
                               .agg({'lat':'sum'})
    
    #добавляем прочих к топ-12
    top13 = pd.concat([top12, other_points])
    
    #создаем столбец для легенды
    top13['labels'] = top13['name'] + " — " + top13['lat'].astype('str')
    return top13


