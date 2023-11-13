from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import csv

#Definicion del driver
def set_driver():
    options = Options()
    options.add_argument("--no-sandbox") #bypass OS security model
    options.add_argument("--headless")
    options.add_argument("--disable-dev-shm-usage") #overcome limited resource problems
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=options)

    # Imprimir el User-Agent utilizado
    user_agent = driver.execute_script("return navigator.userAgent;")
    print(f"User-Agent utilizado: {user_agent}")
    
    return driver

#Funcion para obtener la data de los partidos
def get_partidos(driver, fecha, file_list):
    try:
        # Encuentra todos los elementos con la clase "partdesta jugado"
        partidos = driver.find_elements_by_css_selector(".partdesta.jugado")
        
        for partido in partidos:
            # Obtenemos el estado del partido
            estado_partido_element = partido.find_elements_by_css_selector(".cuando.jugando a")
            estado_partido = estado_partido_element[0].text
            
            # Nos aseguramos que el partido haya finalizado
            if estado_partido == "FINALIZADO":
                # Extrae el nombre de los equipos
                equipo_1 = partido.find_element_by_css_selector(".equi1 a").text
                equipo_2 = partido.find_element_by_css_selector(".equi2 a").text
                # Extrae el resultado del marcador
                marcador = partido.find_element_by_css_selector(".mcdor b").text

                # Extrae la liga de la jornada
                liga = partido.find_element_by_css_selector(".jornada b a").text
                
                # Imprime los resultados
                #print(f"Equipo 1: {equipo_1}, Equipo 2: {equipo_2}, Score: {marcador} , Jornada: {liga}")
                registro = [fecha,liga,equipo_1,equipo_2,marcador]
                #print(registro)
                file_list.append(registro)
                
    except Exception as e:
        # Este error se debe a que aun no se ha renderizado toda la pagina 
        # por lo que no se tiene acceso a find_elements_by_css_selector(".partdesta.jugado")
        # procederemos a esperar 1 segundo a que renderice la pagina y ejecutaremos de nuevo la funcion de obtener partidos
        #print(f"No se pudo obtener los detalles de los partidos en la fecha {fecha}: {str(e)}")
        time.sleep(1)
        file_list = get_partidos(driver, fecha, file_list)
    
    return file_list

#Funcion para generar el CSV
def write_csv(list):
    #Current directory where is located the script
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../dataset"))
    
    if not os.path.exists(path):
        os.makedirs(path)

    filename = "resultado_de_partidos.csv"
    filePath = os.path.join(path, filename)

    with open(filePath, 'w', newline='') as csvFile:
        writer = csv.writer(csvFile)
        for row in list:
            writer.writerow(row)

#Funcion que controla toda la operacion
def get_data():
    
    # Se da la opción al usuario de interrumpir la ejecución del programa
    print("Iniciando scraping...") 
    print("\nPuede interrumpir la ejecución en cualquier momento presionando Ctrl+C.")

    file_list=[]
    headerList=["Fecha","Liga","Equipo1","Equipo2","Resultado"]
    file_list.append(headerList)
    

    # Se permite al usuario introducir el número de jornadas que quiere consultar
    while True:
        try:
            num_dias = int(input("\nPor favor, ingrese la cantidad de días que desea consultar (0-100): "))
            if 0 <= num_dias <= 100:
                break
            else:
                print("Error: Por favor, ingrese un número entero entre 0 y 100.")
        except ValueError:
            print("Error: Por favor, ingrese un número entero.")


    driver = set_driver()
    driver.get("https://www.resultados-futbol.com/")
    #print("Page title was '{}'".format(driver.title))
    fecha_elem = driver.find_element(By.ID, "short_dateLive")
    fecha = fecha_elem.text
    file_list = get_partidos(driver, fecha, file_list)

    #Aqui debemos hacer esto de forma dinamica para que la base de datos sea en base a x cantidad de dias(Dinamica controlada)
    for i in range(num_dias):
        try:
            # Ejecuta JavaScript para hacer clic en "Día anterior"
            driver.execute_script("live_dest_home_data(-1);")
            # Espera hasta que el elemento con ID "short_dateLive" esté presente
            wait = WebDriverWait(driver, 5)
            fecha_element = wait.until(EC.presence_of_element_located((By.ID, "short_dateLive")))

            # Extrae la fecha deseada
            fecha_elem = driver.find_element(By.ID, "short_dateLive")
            fecha = fecha_elem.text

            #Dejamos que la data se cargue correctamente
            time.sleep(0.1)

            file_list = get_partidos(driver, fecha, file_list)
        except Exception as e:
            print(f"No se pudo obtener la data: {str(e)}")

    #print(file_list)
    write_csv(file_list)
    # Cierra el navegador
    driver.quit()


try:    
    get_data()
except KeyboardInterrupt:
    print("\n")
    print("Finalizando programa...")