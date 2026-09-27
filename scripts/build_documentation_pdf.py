"""Genera la memoria técnica y la guía de estudio en PDF. No altera resultados."""

from __future__ import annotations

import csv
from pathlib import Path

from fpdf import FPDF

def _num(text: str, digits: int) -> str:
    return f"{float(text):.{digits}f}".replace(".", ",")


def load_campaign() -> tuple[dict[int, dict[str, str]], dict[int, dict[str, str]]]:
    path = ROOT / "data" / "final_campaign" / "per_run_records.csv"
    go: dict[int, dict[str, str]] = {}
    ac: dict[int, dict[str, str]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            seed = int(row["seed"])
            if row["material"] == "GO":
                go[seed] = row
            elif row["material"] == "AC":
                ac[seed] = row
    return go, ac


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
FIG = ROOT / "data" / "final_campaign" / "figures"
FONT = Path(r"C:\Windows\Fonts\arial.ttf")
FONTB = Path(r"C:\Windows\Fonts\arialbd.ttf")
FONTI = Path(r"C:\Windows\Fonts\ariali.ttf")


class Doc(FPDF):
    def __init__(self, footer_title: str, body: float = 11, lead: float = 5.6) -> None:
        super().__init__(format="A4", unit="mm")
        self.footer_title = footer_title
        self.body = body
        self.lead = lead
        self.set_auto_page_break(auto=True, margin=18)
        self.add_font("Arial", "", str(FONT))
        self.add_font("Arial", "B", str(FONTB))
        self.add_font("Arial", "I", str(FONTI))

    def footer(self) -> None:
        if self.page_no() == 1:
            return
        self.set_y(-12)
        self.set_font("Arial", "", 8)
        self.set_text_color(80, 80, 80)
        self.cell(0, 6, f"{self.footer_title}  ·  {self.page_no()}", align="C")

    def h1(self, text: str, new_page: bool = False) -> None:
        if new_page and self.get_y() > 40:
            self.add_page()
        self.set_x(self.l_margin)
        self.ln(2)
        self.set_font("Arial", "B", 13)
        self.set_text_color(20, 40, 70)
        self.multi_cell(0, 7, text)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def h2(self, text: str) -> None:
        self.set_x(self.l_margin)
        self.ln(1)
        self.set_font("Arial", "B", 11)
        self.multi_cell(0, 6, text)
        self.ln(0.5)

    def p(self, text: str) -> None:
        self.set_x(self.l_margin)
        self.set_font("Arial", "", self.body)
        self.multi_cell(0, self.lead, text)
        self.ln(1.4)

    def bullet(self, text: str) -> None:
        self.set_x(self.l_margin)
        self.set_font("Arial", "", self.body)
        self.multi_cell(0, self.lead, "•  " + text)
        self.ln(0.5)

    def eq(self, text: str) -> None:
        self.set_font("Arial", "I", 10)
        self.multi_cell(0, 5, text, align="C")
        self.ln(1.2)

    def caption(self, text: str) -> None:
        self.set_font("Arial", "I", 8)
        self.set_text_color(60, 60, 60)
        self.multi_cell(0, 4, text)
        self.set_text_color(0, 0, 0)
        self.ln(1.5)

    def fig(self, name: str, caption: str, h: float = 62) -> None:
        path = FIG / name
        if not path.is_file():
            self.p(f"[Figura no encontrada: {name}]")
            return
        if self.get_y() + h + 12 > 280:
            self.add_page()
        self.image(str(path), x=18, w=174, h=h)
        self.ln(1)
        self.caption(caption)

    def table(self, headers: list[str], rows: list[list[str]], widths: list[float]) -> None:
        def room(height: float) -> None:
            if self.get_y() + height > self.h - self.b_margin - 4:
                self.add_page()

        room(12)
        self.set_font("Arial", "B", 8)
        self.set_fill_color(230, 236, 242)
        self.set_x(self.l_margin)
        for h, w in zip(headers, widths):
            self.cell(w, 6, h, border=1, fill=True)
        self.ln()
        self.set_font("Arial", "", 8)
        for row in rows:
            room(6)
            self.set_x(self.l_margin)
            for val, w in zip(row, widths):
                self.cell(w, 5.5, val, border=1)
            self.ln()
        self.set_x(self.l_margin)
        self.ln(2)


def build_memory() -> Doc:
    pdf = Doc("Simulación computacional MB–GO / MB–AC", body=11, lead=5.6)
    pdf.add_page()
    pdf.ln(28)
    pdf.set_font("Arial", "B", 18)
    pdf.multi_cell(0, 9, "Simulación computacional de la adsorción de azul de metileno mediante óxido de grafeno y carbón activado", align="C")
    pdf.ln(6)
    pdf.set_font("Arial", "I", 12)
    pdf.multi_cell(
        0,
        6,
        "Modelo mesoscópico bidimensional basado en movimiento browniano, contacto geométrico, adsorción y análisis cinético",
        align="C",
    )
    pdf.ln(12)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, "Memoria técnica del modelo y de la campaña final", align="C")
    pdf.ln(8)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(
        0,
        5,
        "Documento descriptivo del estado final del repositorio.\nNo constituye validación experimental.",
        align="C",
    )

    pdf.add_page()
    pdf.h1("Contenido")
    for line in [
        "1. Resumen",
        "2. Introducción y objetivos",
        "3. Planteamiento y fundamento",
        "4. Modelo computacional",
        "5. Langmuir y cinética de pseudo-segundo orden",
        "6. Arquitectura del software",
        "7. Recorrido metodológico",
        "8. Validaciones",
        "9. Sensibilidad y protocolo",
        "10. Campaña final y resultados",
        "11. Estadística, masa y reproducibilidad",
        "12. Limitaciones, interpretación y conclusiones",
        "Anexo. Parámetros y bibliografía citada",
    ]:
        pdf.bullet(line)

    pdf.h1("1. Resumen")
    pdf.p(
        "El proyecto implementa un modelo computacional bidimensional y mesoscópico de la adsorción de azul de metileno (MB) sobre óxido de grafeno (GO) y sobre carbón activado (AC). No es una simulación molecular, atomística ni cuántica: cada «partícula» es un objeto discreto que representa una porción de masa, no una molécula resuelta."
    )
    pdf.p(
        "El ciclo de cada paso es: desplazamiento aleatorio, detección geométrica de contacto y, si hay capacidad, adsorción del objeto MB completo. La cantidad adsorbida se expresa como qt (mg/g). Los modelos de Langmuir y de pseudo-segundo orden (PSO) se calculan aparte y sirven de referencia; el motor no se detiene ni se ajusta para alcanzar un qe dado."
    )
    pdf.p(
        "La campaña final comprende 80 realizaciones (40 semillas para GO y 40 para AC), con geometría de referencia, sigma = 1,5 px/paso, 2000 pasos y regla de adsorción P_ads = 1. En esas condiciones, la media de objetos MB adsorbidos es 187,45 sobre GO (93,73 %; qt = 374,9 mg/g) y 133,175 sobre AC (66,59 %; qt = 266,35 mg/g). La diferencia de medias es de 54,3 objetos y 108,5 mg/g. Estos números describen el modelo, no un experimento de laboratorio."
    )

    pdf.h1("2. Introducción y objetivos")
    pdf.p(
        "El problema de partida es representar, en un recinto bidimensional, el encuentro entre azul de metileno y un adsorbente, y registrar cuánta masa queda asociada al sólido. El objetivo operativo es disponer de un motor reproducible, separable de la visualización, capaz de comparar GO y AC bajo el mismo protocolo de ejecución."
    )
    pdf.h2("Objetivos cumplidos en el repositorio")
    pdf.bullet("Definir un dominio, masas, capacidades y una geometría de contacto explícita.")
    pdf.bullet("Separar movimiento, contacto y adsorción, con pruebas automáticas.")
    pdf.bullet("Tratar Langmuir y PSO como referencias externas, no como objetivo de ajuste.")
    pdf.bullet("Explorar sigma, horizonte de pasos, geometría y la regla P_ads antes de fijar un protocolo.")
    pdf.bullet("Ejecutar una campaña final de 40+40 semillas y conservar series, agregados y figuras.")

    pdf.h1("3. Planteamiento y fundamento")
    pdf.p("La cadena implementada es la siguiente.")
    pdf.eq("movimiento browniano  →  contacto geométrico  →  adsorción  →  qt  →  comparación con referencias")
    pdf.p(
        "Lo que el modelo no incluye: disolvente molecular, estructura atómica del GO o del AC, difusión con coeficiente D calibrado en m²/s, transferencia de calor, pH dinámico, ni una probabilidad de adhesión medida para estos materiales. La temperatura (25 °C), el pH (6), el volumen (40 mL) y las masas entran como condiciones de contorno y de balance, no como campos resueltos en el recinto."
    )
    pdf.h2("Cuatro clases de magnitudes")
    pdf.bullet("Bibliográficas o de condición de referencia: T, pH, masas, volumen, qmax, KL, qe y Ce de Langmuir, qe y k2 de PSO, y la referencia S* = 0,55. qe y Ce no son condiciones de operación: son el equilibrio de referencia.")
    pdf.bullet("Derivadas: C0 = 4 mg / 0,04 L = 100 mg/L; masa por objeto MB = 0,02 mg; capacidad por unidad de adsorbente. C0 no es un dato bibliográfico aparte de ese cociente.")
    pdf.bullet("Computacionales de ejecución: sigma (px/paso), número de pasos, semilla, P_ads y número de repeticiones.")
    pdf.bullet("De representación: lado en píxeles, círculo inscrito y escala 77,4 μm/px asociada a un lado de recipiente de 3,42 cm.")

    pdf.h1("4. Modelo computacional")
    pdf.h2("4.1 Dominio y objetos")
    pdf.p(
        "El recinto final es un cuadrado de 442×442 px. Hay 200 objetos MB y 100 unidades de adsorbente. En la geometría final, el MB ocupa 1×1 px (radio de contacto 0,5 px), el GO 7×7 px (radio 3,5 px, móvil) y el AC 2×2 px (radio 1,0 px, fijo). El umbral de contacto es la suma de radios: 4,0 px para MB–GO y 1,5 px para MB–AC. Estas medidas no son tamaños moleculares."
    )
    pdf.table(
        ["Objeto", "Lado", "Radio", "Movilidad", "Contacto con MB"],
        [
            ["MB", "1×1 px", "0,5 px", "Libre", "—"],
            ["GO", "7×7 px", "3,5 px", "Móvil", "≤ 4,0 px"],
            ["AC", "2×2 px", "1,0 px", "Fijo", "≤ 1,5 px"],
        ],
        [28, 32, 32, 40, 48],
    )
    pdf.caption(
        "Tabla 1. Geometría final de representación. Los radios son los del círculo inscrito en el cuadrado. No son radios moleculares."
    )
    pdf.p(
        "El lado de 442 px se asocia a un lado de recipiente de 3,42 cm, con escala 77,4 μm/px. Esa escala sitúa el recinto; no convierte el lado de un objeto en un diámetro experimental del sólido o del colorante."
    )
    pdf.p(
        "Una geometría anterior, archivada y no sobrescrita, usaba MB de 5×5 px y adsorbente de 7×7 px tanto para GO como para AC. Los resultados de esa era no se mezclan con la campaña final."
    )
    pdf.h2("4.2 Movimiento")
    pdf.p("En cada paso, los objetos libres reciben un incremento independiente:")
    pdf.eq("Δx, Δy  ~  Normal(0, σ²)     con σ en px/paso")
    pdf.p(
        "Sigma no está identificado con un coeficiente de difusión experimental. En la campaña final σ = 1,5 px/paso. Si el adsorbente es móvil (GO), recibe el mismo tipo de incremento; si es fijo (AC), no se desplaza. El choque con el borde es una reflexión del exceso y un recorte al recinto: es una regla numérica, no una ley extraída de un ensayo."
    )
    pdf.h2("4.3 Contacto y adsorción")
    pdf.p(
        "El contacto es geométrico y determinista: un MB libre contacta una unidad de adsorbente si la distancia entre centros es menor o igual que r_MB + r_adsorbente. No hay probabilidad de colisión. Si un MB toca varias unidades, se considera la más cercana con capacidad (empate: índice menor)."
    )
    pdf.p(
        "La adsorción transfiere el objeto entero (0,02 mg) si la capacidad restante de esa unidad es al menos esa masa. No se adsorben fracciones de objeto. Si un objeto toca varias unidades, se asigna a la más cercana que aún admite ese peso; si hay empate de distancia, se elige el índice menor. Con P_ads = 1 la transferencia ocurre siempre que haya capacidad, y no se extrae un número aleatorio extra. Con 0 < P_ads < 1 se aplica un ensayo de Bernoulli después del filtro de capacidad; ese ensayo consume aleatoriedad y puede cambiar la trayectoria posterior. P_ads = 0 rechaza el contacto sin extraer aleatoriedad. P_ads = 1 es la regla de la campaña final. No es una probabilidad de sticking medida."
    )
    pdf.p(
        "El valor bibliográfico S* = 0,55 (Sha'Ato, 2021, carbón activo obtenido de polifurfurilo y azul de metileno) se conserva solo como contexto. No se sustituyó P_ads por S*, ni se afirma que ese carbón sea el mismo que el del modelo. Un barrido aparte evaluó P_ads = 0,55 como escenario numérico, no como calibración."
    )
    pdf.h2("4.4 Orden de un paso")
    pdf.p(
        "Cada paso sigue una sola ruta, la misma en el cálculo por lotes y en la ventana: desplazar, detectar contactos, adsorber, anotar. El desplazamiento usa un generador aleatorio inicializado con la semilla. Solo se mueven los objetos MB que siguen libres y, si el adsorbente es el GO, también las unidades de GO. El AC permanece en su sitio. Después del salto, si una coordenada sale del cuadrado, el exceso se refleja y el resultado se recorta al recinto. Es una regla numérica de borde."
    )
    pdf.p(
        "El contacto no vuelve a sortear nada: cuenta pares cuya distancia entre centros es menor o igual que la suma de radios, y suma esos pares al contador de contactos del paso. La adsorción actúa sobre esos pares. Langmuir y PSO no se consultan en esta decisión. Al final del paso se guarda una instantánea de qt, masas y recuentos. La colocación inicial reparte los objetos al azar, con la semilla, rechazando solapes de los cuadrados."
    )
    pdf.h2("4.5 Capacidad y qt")
    pdf.p(
        "La capacidad de cada unidad es qmax multiplicado por su masa. Con 10 mg de adsorbente repartidos en 100 unidades, cada unidad pesa 0,1 mg. qt es la masa adsorbida dividida por la masa de adsorbente (mg/g). También se registran la masa libre, el porcentaje de objetos adsorbidos y el número de contactos. Contactos y adsorciones no coinciden: un contacto no consume un MB si la unidad ya no admite otro objeto entero o, cuando P_ads es menor que 1, si el ensayo aleatorio lo rechaza."
    )
    pdf.p(
        "Como solo se transfiere el objeto completo de 0,02 mg, la capacidad no se aprovecha hasta el último miligramo. Con qmax del GO (764,7 mg/g), cada unidad admite 0,07647 mg, es decir tres objetos, y quedan 0,01647 mg que no bastan para un cuarto. Con qmax del AC (412,2 mg/g), cada unidad admite dos objetos. El techo global es 300 objetos en GO y 200 en AC. La campaña final no alcanza esos techos (máximos observados: 196 y 144). En este protocolo, el límite visible es el número de encuentros, no el agotamiento de qmax del conjunto."
    )
    pdf.eq("qt (mg/g) = (Nads × 0,02 mg) / 0,010 g")
    pdf.p(
        "Por eso Nads, la masa adsorbida y qt son la misma información a distinta escala. Para la media de GO, 187,45 × 0,02 mg = 3,749 mg y qt = 374,9 mg/g. Para la media de AC, 133,175 × 0,02 mg = 2,6635 mg y qt = 266,35 mg/g. La masa libre es 4 mg menos la masa adsorbida."
    )

    pdf.h1("5. Langmuir y cinética de pseudo-segundo orden")
    pdf.h2("5.1 Langmuir (equilibrio de referencia)")
    pdf.eq("qe = qmax · KL · Ce / (1 + KL · Ce)")
    pdf.p(
        "El código puede resolver además el equilibrio conjunto con el balance de masa (C0 − Ce)·V/m. Los valores adoptados como referencia documentada, y que la simulación no está obligada a reproducir, son:"
    )
    pdf.table(
        ["", "qmax (mg/g)", "KL (L/mg)", "qe (mg/g)", "Ce (mg/L)"],
        [
            ["GO", "764,7", "0,206", "380,7", "4,81"],
            ["AC", "412,2", "0,088", "290,9", "27,3"],
        ],
        [22, 38, 36, 36, 36],
    )
    pdf.p(
        "En la campaña final, el qt medio de GO (374,9 mg/g) queda cerca de 380,7 mg/g, pero el máximo entre semillas es 392 mg/g, por encima de ese qe. El motor no corrige ese exceso: es un modelo discreto y estocástico. El qt de AC (media 266,35 mg/g; rango 240–288) queda por debajo del qe de Langmuir de AC (290,9 mg/g) sin haber sido forzado a él."
    )
    pdf.h2("5.2 PSO (cinética de referencia)")
    pdf.eq("qt(t) = (k2 · qe² · t) / (1 + k2 · qe · t)     t en minutos")
    pdf.table(
        ["", "qe_PSO (mg/g)", "k2 (g/(mg·min))"],
        [
            ["GO", "384,6", "0,0002"],
            ["AC", "100,4", "0,00910"],
        ],
        [30, 50, 70],
    )
    pdf.p(
        "Cada material usa solo sus parámetros. La curva de GO no se aplica al AC ni al revés. Para el GO el repositorio guarda dos k2 distintos y no unificados: 0,0002 en la curva PSO de referencia y 0,001 en otra tabla. La curva usa 0,0002 porque es el valor con el que el cálculo de referencia cierra a 10 min y 1,672 mg. Esta discrepancia pertenece a la información disponible en el repositorio. No se ha hecho una nueva validación bibliográfica para resolverla, ni se ha sustituido un valor por el otro. El eje de las figuras de simulación son pasos. Las figuras PSO usan minutos y están etiquetadas como referencia."
    )
    pdf.p(
        "El tiempo de laboratorio asociado a una fracción f de qe_PSO, con 0 < f < 1, es t(f) = f / (k2 · qe · (1 − f)), en minutos. Un análisis exploratorio define α = t_PSO / n_sim (min/paso) cuando la serie simulada alcanza esa fracción, sin extrapolar más allá del horizonte. α no es constante entre materiales ni entre fracciones, y no convierte los pasos de la campaña en minutos. El qe_PSO del AC (100,4 mg/g) está muy por debajo del qt simulado (~266 mg/g); por eso las fracciones respecto de ese qe se cruzan pronto y no deben leerse como un reloj validado."
    )
    pdf.fig(
        "12_pso_reference_go_minutes.png",
        "Figura 1. Curva PSO de referencia del GO (minutos). No es la trayectoria de la simulación.",
        58,
    )
    pdf.fig(
        "13_pso_reference_ac_minutes.png",
        "Figura 2. Curva PSO de referencia del AC, con sus propios qe y k2.",
        58,
    )

    pdf.h1("6. Arquitectura del software")
    pdf.p(
        "El cálculo vive en el paquete src/go_mb/. La ventana, las campañas y las figuras llaman a las mismas funciones de avance; no hay un segundo motor. tests/ contiene las comprobaciones del programa, sin abrir la interfaz. data/ conserva cada campaña en su carpeta. docs/ recoge lo que sigue sin identificación física. packaging/ y el archivo scripts/build_windows.ps1 sirven para empaquetar el ejecutable de presentación. El resto de scripts/ son herramientas auxiliares: generación de documentación, apertura de la visualización, comprobación del entorno gráfico y un lote histórico de caracterización del carbón. No empaquetan el programa y no cambian masas, geometría ni la regla de adsorción."
    )
    pdf.table(
        ["Módulo", "Función en el proyecto"],
        [
            ["config, state", "Condiciones, geometría y estado de los objetos"],
            ["motion, contact", "Salto normal y umbral de distancia"],
            ["adsorption, engine", "Orden del paso y transferencia de masa"],
            ["metrics, models", "qt, Langmuir, PSO y resúmenes"],
            ["stats, io", "Media, dispersión, IC 95 % y guardado"],
            ["sensitivity y campañas", "Barridos, mallas temporales y campaña final"],
            ["interactive, launcher", "Misma función de avance, con pausa y reinicio"],
        ],
        [48, 132],
    )
    pdf.caption("Tabla 2. Relación entre piezas. Las campañas escriben CSV, JSON y figuras; no reescriben el motor.")
    pdf.p(
        "Una corrida se identifica por material, semilla, sigma, número de pasos y P_ads. El JSON de cada semilla guarda la serie; el CSV de campaña reúne el final de cada corrida; statistics.json y comparison_go_ac.csv reúnen los agregados. Repetir una simulación exige esos cinco datos. El nombre de la carpeta no basta."
    )

    pdf.h1("7. Recorrido metodológico", new_page=True)
    pdf.p(
        "El protocolo final no se eligió al principio. Cada etapa respondía a una pregunta y dejaba los datos anteriores intactos. Lo que sigue es el orden real del repositorio."
    )
    pdf.h2("7.1 Definición y primer motor")
    pdf.p(
        "Se fijó un recinto, 200 objetos de colorante y 100 unidades de adsorbente, con Langmuir y PSO fuera del detector de contacto. El primer motor ya separaba movimiento, contacto geométrico y adsorción del objeto entero. Quedó explícito que sigma, el número de pasos y P_ads no tenían valor físico cerrado."
    )
    pdf.h2("7.2 Sensibilidad de sigma y de pasos")
    pdf.p(
        "Se barrieron sigma y el horizonte de pasos para ver si el resultado final dependía de ellos. La clasificación de esa etapa es exploración computacional, no validación experimental. No se eligió un coeficiente de difusión ni se igualaron los pasos a minutos."
    )
    pdf.h2("7.3 Malla temporal homogénea")
    pdf.p(
        "Para comparar GO y AC con la misma malla se usaron dos valores de sigma (1,0 y 1,5 px/paso), siete horizontes (200, 400, 600, 800, 1000, 1500 y 2000 pasos) y cinco semillas (1 a 5). Son 70 corridas por material y 140 por era geométrica. La pregunta era si la adsorción seguía creciendo al alargar el horizonte. El crecimiento se frena hacia 1000–2000 pasos, sin una meseta estricta en todo el intervalo. Esa serie usa la geometría anterior y permanece archivada."
    )
    pdf.h2("7.4 Cambio de geometría")
    pdf.p(
        "La representación pasó a MB 1×1, GO 7×7 móvil y AC 2×2 fijo. La malla de 140 corridas se repitió en una carpeta nueva, sin borrar la anterior. La decisión fue no mezclar eras: un número obtenido con MB de 5×5 px no se compara en la misma tabla con la campaña final."
    )
    pdf.h2("7.5 Escala temporal exploratoria")
    pdf.p(
        "Se cruzaron las series ya calculadas con la curva PSO de cada material y se estimó α = t_PSO / n_sim en las fracciones alcanzadas. Al principio el AC no tenía curva propia; cuando se incorporó, dejó de reutilizarse la del GO. α no se fijó. Quedó descartada cualquier frase del tipo «2000 pasos equivalen a tantos minutos»."
    )
    pdf.h2("7.6 Regla P_ads y referencia S*")
    pdf.p(
        "Se ejecutó un barrido con P_ads en {0,25; 0,50; 0,75; 1,00}, sigma 1,0 y 1,5, 2000 pasos y semillas 1 a 5, en GO y en AC (80 corridas). El barrido cambia la adsorción media y también los contactos medios, porque el ensayo aleatorio consume la misma fuente de azar y desvía la trayectoria. No es una relación monótona en todas las celdas: en GO, con sigma 1,0, la media a P_ads = 1,0 queda por debajo de la media a P_ads = 0,75, y con sigma 1,5 la media a P_ads = 0,50 queda por encima de 0,75 y de 1,0. Por eso no puede decirse que bajar P_ads disminuya siempre la adsorción, ni que los contactos sean independientes de P_ads. Un complemento de 20 corridas usó P_ads = 0,55 solo como escenario junto a la referencia bibliográfica S* = 0,55. No se declaró un P_ads «correcto». La campaña final mantuvo P_ads = 1 como decisión computacional, no como probabilidad experimental."
    )
    pdf.h2("7.7 Protocolo que sí se cerró")
    pdf.p(
        "Con la geometría final, σ = 1,5 px/paso, 2000 pasos y P_ads = 1 se lanzaron las semillas 1 a 40 de cada material. Durante esa campaña no se reajustaron parámetros ni se reinterpretaron corridas a mitad de camino. Lo que sigue sin cerrar, y así consta en la lista de pendientes, es la identificación física de sigma, la equivalencia pasos–minutos, un P_ads bibliográfico de estos materiales y la unificación del k2 de GO."
    )
    pdf.p(
        "Quedó descartado usar la curva PSO de un material para el otro, forzar el motor hacia qe, interpretar 100 mg/g como concentración (el valor retenido es 100 mg/L) y tratar S* como sustituto de P_ads."
    )

    pdf.h1("8. Validaciones")
    pdf.p(
        "El repositorio contiene 135 funciones de prueba identificadas en tests/. Cubren, entre otras cosas, conservación de masa, reproducibilidad con la misma semilla, contacto geométrico, adsorción con P_ads = 0 y P_ads = 1, geometría final frente a la anterior, campañas reducidas, calibración temporal (fracción no alcanzada sin extrapolación), paridad entre la sesión gráfica y el motor sin ventana, pausa (no avanza el estado) y reinicio (misma semilla, misma trayectoria). Esta memoria no vuelve a ejecutarlas."
    )
    pdf.p(
        "En las 80 corridas finales, el indicador de conservación de masa es verdadero en todas: la masa adsorbida más la masa libre recuperan los 4 mg iniciales, dentro de la tolerancia del motor. Con P_ads = 1, el número de eventos de adsorción coincide con Nads; el número de contactos es mayor en las 80 corridas."
    )
    pdf.p(
        "La comparación entre la sesión gráfica y el cálculo sin ventana usa la misma semilla y la misma función de avance. Pausar no incrementa el estado. Reiniciar con la misma semilla reproduce la trayectoria. Las entradas de la ventana se validan antes de lanzar la corrida; los campos de condición experimental se muestran y no se editan desde esa pantalla."
    )

    pdf.h1("9. Sensibilidad y protocolo")
    pdf.p(
        "Antes de la campaña final se observó que alargar el horizonte frena el crecimiento de objetos adsorbidos, sobre todo hacia 1000–2000 pasos, sin una meseta estricta en todo el intervalo. Sigma = 1,5 tiende a adsorber más que sigma = 1,0 en la geometría final, con la reserva de que la relación no se impuso como ley. El barrido de P_ads cambia la adsorción y las trayectorias, pero en GO la media no sigue siempre una relación monótona al subir o bajar P_ads. Los rechazos aleatorios también cambian el número de contactos. Por eso la sensibilidad no es solo una conversión contacto→adsorción, ni una regla de «a menor P_ads, menor adsorción»."
    )
    pdf.p(
        "El protocolo autorizado para la campaña definitiva no se reoptimizó durante la ejecución: geometría final, σ = 1,5, 2000 pasos, P_ads = 1, semillas 1 a 40, condiciones T = 25 °C, pH = 6, 4 mg de MB, 10 mg de adsorbente, 40 mL y C0 = 100 mg/L."
    )

    pdf.h1("10. Campaña final y resultados", new_page=True)
    pdf.p(
        "Clasificación interna: campaña computacional final, no validación experimental. Cada corrida guarda semilla, sigma, pasos, P_ads, Nads, porcentaje, qt, masas, contactos, eventos de adsorción, eficiencia y conservación de masa (data/final_campaign/)."
    )
    pdf.table(
        ["Métrica", "GO media", "AC media", "Δ (GO−AC)"],
        [
            ["Nads", "187,45", "133,175", "+54,3"],
            ["% adsorbido", "93,73", "66,59", "+27,1"],
            ["qt (mg/g)", "374,9", "266,35", "+108,5"],
            ["Contactos", "605,7", "320,8", "+284,9"],
            ["Ads./contacto", "0,317", "0,421", "−0,105"],
            ["m ads. (mg)", "3,749", "2,6635", "+1,0855"],
        ],
        [42, 40, 42, 46],
    )
    pdf.caption("Tabla 3. Medias de la campaña final (40 semillas por material), a partir de comparison_go_ac.csv.")
    pdf.p(
        "GO adsorbe más objetos y acumula más contactos. La eficiencia contacto→adsorción es mayor en AC (menos contactos por cada adsorción). Contactos y adsorciones no son intercambiables: en esta campaña, con P_ads = 1, el número de eventos de adsorción coincide con Nads, pero el número de contactos es claramente mayor."
    )
    pdf.fig(
        "01_nads_by_seed_go_vs_ac.png",
        "Figura 3. Nads final por semilla. Cada punto es una realización independiente del mismo protocolo.",
        62,
    )
    pdf.fig(
        "02_qt_by_seed_go_vs_ac.png",
        "Figura 4. qt final (mg/g) por semilla. El eje no está en minutos.",
        62,
    )
    pdf.fig(
        "07_contact_to_adsorption_efficiency.png",
        "Figura 5. Cociente eventos de adsorción / contactos. No es una probabilidad física medida.",
        55,
    )
    pdf.fig(
        "06_contacts_by_seed.png",
        "Figura 6. Contactos por semilla. La dispersión de contactos es mayor que la de Nads (apartado 11).",
        55,
    )
    pdf.fig(
        "04_nads_distribution.png",
        "Figura 7. Distribución de Nads. GO queda por encima de AC, con solapamiento nulo entre los rangos de la campaña (171–196 frente a 120–144).",
        55,
    )
    pdf.fig(
        "10_qt_vs_langmuir_go.png",
        "Figura 8. qt de GO frente a la línea de qe de Langmuir (380,7 mg/g). Algunas semillas quedan por encima.",
        55,
    )
    pdf.fig(
        "11_qt_vs_langmuir_ac.png",
        "Figura 9. qt de AC frente a su qe de Langmuir (290,9 mg/g). El rango de la campaña (240–288 mg/g) queda por debajo.",
        55,
    )

    pdf.h1("11. Estadística, masa y reproducibilidad")
    pdf.p(
        "Sobre 40 semillas, el coeficiente de variación de Nads es 2,53 % en GO y 4,20 % en AC. Los contactos varían más (CV 14,9 % en GO y 12,3 % en AC). El intervalo de confianza al 95 % usa el estadístico t ya implementado (n = 40, t crítico = 2,023). Describe la media del modelo, no un error de laboratorio."
    )
    pdf.table(
        ["Media", "IC 95 % GO", "IC 95 % AC"],
        [
            ["Nads", "185,93 – 188,97", "131,39 – 134,96"],
            ["qt (mg/g)", "371,86 – 377,94", "262,78 – 269,92"],
            ["Contactos", "576,75 – 634,55", "308,18 – 333,42"],
        ],
        [40, 70, 70],
    )
    pdf.caption("Tabla 4. Intervalos de confianza al 95 % de la media, tomados de statistics.json. Redondeados a dos decimales.")
    pdf.table(
        ["", "mediana", "mín.", "máx.", "p25", "p75", "CV %"],
        [
            ["GO Nads", "187,5", "171", "196", "185", "190", "2,53"],
            ["AC Nads", "133", "120", "144", "129", "136,75", "4,20"],
            ["GO qt", "375", "342", "392", "370", "380", "2,53"],
            ["AC qt", "266", "240", "288", "258", "273,5", "4,20"],
        ],
        [28, 24, 22, 22, 24, 24, 22],
    )
    pdf.caption("Tabla 5. Dispersión de Nads y qt. El CV de qt coincide con el de Nads porque qt es proporcional a Nads.")
    pdf.p(
        "La misma semilla y la misma configuración reproducen la serie. Los resultados individuales están en per_run_records.csv y en los JSON de cada corrida. La procedencia del protocolo está en provenance.json. Repetir una simulación exige material, semilla, sigma, pasos y P_ads; no basta el nombre de la campaña."
    )
    pdf.fig(
        "08_qt_evolution_go_vs_steps.png",
        "Figura 10. Evolución de qt del GO frente a pasos (40 semillas). El eje temporal es computacional.",
        58,
    )
    pdf.fig(
        "09_qt_evolution_ac_vs_steps.png",
        "Figura 11. Evolución de qt del AC frente a pasos, con el mismo horizonte de 2000 pasos.",
        58,
    )

    pdf.h1("12. Limitaciones, interpretación y conclusiones")
    pdf.h2("Limitaciones")
    pdf.bullet("Modelo 2D, mesoscópico y discreto: no resuelve moléculas ni el disolvente.")
    pdf.bullet("Sigma y el número de pasos son parámetros de ejecución, no una escala física demostrada.")
    pdf.bullet("P_ads = 1 es una regla computacional. S* = 0,55 no la sustituye.")
    pdf.bullet("Langmuir y PSO orientan la lectura; no restringen el motor.")
    pdf.bullet("Cuarenta semillas cuantifican la dispersión del modelo, no un error experimental.")
    pdf.bullet("La geometría en píxeles no debe leerse como tamaño real del sólido o del colorante.")
    pdf.h2("Interpretación")
    pdf.p(
        "Bajo el protocolo final, el GO móvil y de mayor radio de contacto retiene más azul de metileno que el AC fijo y más pequeño. Esa diferencia es coherente con más encuentros geométricos, no con una demostración de mecanismo químico. Parte del qt de GO se sitúa junto al qe de Langmuir e incluso lo supera en algunas semillas; eso indica coincidencia numérica parcial, no ajuste del modelo al equilibrio."
    )
    pdf.h2("Conclusiones")
    pdf.bullet("El motor es reproducible y conserva la masa en las 80 corridas finales.")
    pdf.bullet("GO: media 187,45 objetos adsorbidos, 93,73 %, qt 374,9 mg/g, 605,7 contactos.")
    pdf.bullet("AC: media 133,175 objetos, 66,59 %, qt 266,35 mg/g, 320,8 contactos.")
    pdf.bullet("La comparación es descriptiva. No establece causalidad experimental ni un ranking de materiales fuera del modelo.")
    pdf.h2("Trabajo no cerrado dentro del propio código")
    pdf.p(
        "Siguen abiertos, según docs/PENDIENTES.md, la identificación física de sigma, la equivalencia pasos–minutos, un P_ads bibliográfico propio de estos materiales y la discrepancia del k2 de GO (0,0002 en la curva de referencia frente a 0,001 en la otra tabla). No se ha resuelto esa discrepancia con una validación bibliográfica nueva. La campaña de 40+40 ya está ejecutada y no fue recalculada para este documento."
    )

    pdf.h1("13. Lectura de las figuras y glosario")
    pdf.p(
        "Las figuras de la campaña están en la carpeta de resultados finales. Este documento inserta las que resumen la comparación, la dispersión, el equilibrio de referencia y la evolución. El resto existe y dice lo mismo en otra escala: el porcentaje por semilla, el histograma de qt y las curvas PSO ya mostradas en el apartado 5."
    )
    pdf.bullet("Por semilla (figuras 3, 4 y 6): cada punto es una realización. No es una serie temporal.")
    pdf.bullet("Distribución (figura 7): los rangos de Nads de GO y de AC no se solapan en esta campaña.")
    pdf.bullet("Frente a Langmuir (figuras 8 y 9): la línea horizontal es qe de referencia, no un objetivo de la corrida.")
    pdf.bullet("Evolución (figuras 10 y 11): el eje horizontal son pasos. No se lee en minutos.")
    pdf.h2("Símbolos usados")
    pdf.table(
        ["Símbolo", "Significado en este proyecto"],
        [
            ["Nads", "Objetos MB adsorbidos al final de la corrida"],
            ["qt", "Masa adsorbida / masa de adsorbente (mg/g)"],
            ["σ", "Desviación del salto, en px/paso. No es un D medido"],
            ["P_ads", "Regla computacional tras el contacto. Campaña: 1"],
            ["S*", "Sticking bibliográfico 0,55. No sustituye a P_ads"],
            ["qmax, KL", "Parámetros de la isoterma de Langmuir de referencia"],
            ["qe, Ce", "Equilibrio de referencia, no el final obligatorio"],
            ["k2", "Constante PSO, en g/(mg·min), sobre minutos de laboratorio"],
            ["α", "t_PSO / n_sim, exploratorio, no constante física"],
        ],
        [32, 148],
    )

    pdf.h1("Anexo A. Resultados individuales", new_page=True)
    pdf.p(
        "Cada fila es una semilla. Los dos materiales comparten el número de semilla, pero son realizaciones distintas. Todas conservan la masa. Fuente: per_run_records.csv."
    )
    go, ac = load_campaign()
    rows_qt = []
    rows_c = []
    for seed in range(1, 41):
        g = go[seed]
        a = ac[seed]
        rows_qt.append(
            [
                str(seed),
                g["n_adsorbed"],
                _num(g["qfinal_mg_g"], 0),
                a["n_adsorbed"],
                _num(a["qfinal_mg_g"], 0),
            ]
        )
        rows_c.append(
            [
                str(seed),
                g["n_contacts"],
                _num(g["contact_to_adsorption_efficiency"], 3),
                a["n_contacts"],
                _num(a["contact_to_adsorption_efficiency"], 3),
            ]
        )
    pdf.table(
        ["Semilla", "Nads GO", "qt GO", "Nads AC", "qt AC"],
        rows_qt,
        [28, 36, 36, 36, 36],
    )
    pdf.caption("Tabla 6. Nads y qt (mg/g) de las 80 corridas. qt = Nads × 0,02 mg / 0,010 g.")
    pdf.table(
        ["Semilla", "Cont. GO", "Efic. GO", "Cont. AC", "Efic. AC"],
        rows_c,
        [28, 36, 36, 36, 36],
    )
    pdf.caption(
        "Tabla 7. Contactos y cociente adsorciones/contactos. La eficiencia no es una probabilidad medida."
    )

    pdf.h1("Anexo B. Parámetros de la campaña final", new_page=True)
    pdf.table(
        ["Magnitud", "Valor", "Tipo"],
        [
            ["T / pH", "25 °C / 6", "Condición"],
            ["MB / adsorbente / V", "4 mg / 10 mg / 40 mL", "Condición"],
            ["C0", "100 mg/L", "Derivada"],
            ["N MB / N adsorbente", "200 / 100", "Computacional"],
            ["Dominio", "442 px; 3,42 cm", "Representación"],
            ["MB, GO, AC", "1×1, 7×7, 2×2 px", "Representación"],
            ["sigma / pasos / P_ads", "1,5 / 2000 / 1", "Ejecución"],
            ["Semillas", "1…40 por material", "Ejecución"],
        ],
        [55, 62, 53],
    )
    pdf.h2("Bibliografía citada en el repositorio")
    pdf.p(
        "Sha'Ato, R. (2021). Isotherms, Kinetics and Thermodynamics of Methylene Blue Adsorption on Active Carbon from Polyfurfuryl Alcohol. Nigerian Journal of Chemical Research, 25(1). De este trabajo se toma únicamente S* = 0,55, como referencia de un sistema relacionado de carbón activo y azul de metileno. No se transcriben aquí isotermas ni cinéticas de ese artículo, y S* no entra en la campaña final."
    )
    pdf.p(
        "Los valores de qmax, KL, qe, Ce y de los parámetros PSO están almacenados como referencia del proyecto en el código de condiciones. Este documento no reconstruye la bibliografía experimental de la que proceden más allá de lo que el repositorio guarda."
    )
    pdf.p(
        "Fuentes de cifras: comparación y estadísticos de la campaña final, registro de procedencia, módulos de movimiento, contacto, adsorción y referencias de Langmuir y PSO, y la lista de parámetros aún abiertos. El índice de archivos está en docs/fuentes_documentacion.md."
    )
    return pdf


def build_guide() -> Doc:
    pdf = Doc("Guía de estudio — modelo MB–GO / MB–AC", body=12, lead=6.6)
    pdf.add_page()
    pdf.ln(18)
    pdf.set_font("Arial", "B", 16)
    pdf.multi_cell(0, 8, "Guía de estudio", align="C")
    pdf.ln(3)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(
        0,
        6,
        "Simulación bidimensional de adsorción de azul de metileno\nsobre óxido de grafeno y carbón activado",
        align="C",
    )
    pdf.ln(6)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(0, 5, "Documento de repaso. Complementa la memoria técnica; no añade resultados.", align="C")

    pdf.h1("1. Qué es este modelo, en una frase")
    pdf.p(
        "Es un modelo de objetos en un plano: se mueven al azar, se tocan según la distancia y, si cabe masa, el colorante queda asociado al sólido. No es dinámica molecular."
    )

    pdf.h1("2. La cadena que hay que saber explicar")
    pdf.eq("movimiento  →  contacto  →  adsorción  →  qt  →  comparar con Langmuir y PSO")
    pdf.bullet("Movimiento: saltos gaussianos. No es una trayectoria física calibrada.")
    pdf.bullet("Contacto: distancia ≤ suma de radios. No es una probabilidad.")
    pdf.bullet("Adsorción: se transfiere un objeto entero de 0,02 mg si hay capacidad.")
    pdf.bullet("qt: masa adsorbida / masa de adsorbente, en mg/g.")
    pdf.bullet("Langmuir y PSO: referencias. El programa no se obliga a caer en qe.")

    pdf.h1("3. Condiciones y protocolo final")
    pdf.table(
        ["Concepto", "Valor que hay que recordar"],
        [
            ["Condiciones", "25 °C, pH 6, 4 mg MB, 10 mg sólido, 40 mL"],
            ["C0", "100 mg/L (no 100 mg/g)"],
            ["Objetos", "200 MB y 100 de adsorbente"],
            ["Dibujo final", "MB 1×1, GO 7×7 móvil, AC 2×2 fijo"],
            ["Ejecución", "σ = 1,5 px/paso, 2000 pasos, P_ads = 1"],
            ["Muestra", "40 semillas GO + 40 semillas AC"],
        ],
        [40, 130],
    )

    pdf.h1("4. Números de la campaña (memorizar el orden de magnitud)")
    pdf.table(
        ["", "GO", "AC"],
        [
            ["Nads medio", "187,5 de 200", "133,2 de 200"],
            ["Porcentaje", "93,7 %", "66,6 %"],
            ["qt medio", "375 mg/g", "266 mg/g"],
            ["Contactos", "~606", "~321"],
            ["CV de Nads", "2,5 %", "4,2 %"],
            ["qe Langmuir", "380,7 mg/g", "290,9 mg/g"],
        ],
        [40, 65, 65],
    )
    pdf.p(
        "Diferencia GO − AC: unos 54 objetos y unos 109 mg/g. GO tiene más contactos; AC tiene mayor cociente adsorciones/contactos. No decir que «el contacto equivale a adsorber»."
    )
    pdf.p(
        "Algunas semillas de GO superan 380,7 mg/g (el máximo de campaña es 392). No es un error que haya que corregir: el modelo discreto no está atado al equilibrio de Langmuir."
    )

    pdf.h1("5. Un ejemplo numérico, para no perderse")
    pdf.p(
        "Cada objeto MB pesa 0,02 mg. El adsorbente pesa 0,010 g. Si una corrida adsorbe 180 objetos, la masa adsorbida es 3,60 mg y qt = 3,60 / 0,010 = 360 mg/g. La masa libre es 4,00 − 3,60 = 0,40 mg. Ese es el único paso aritmético que hace falta en la defensa: Nads, miligramos y qt dicen lo mismo."
    )
    pdf.p(
        "La media real de la campaña no es 180. Es 187,45 en GO (3,749 mg; 374,9 mg/g) y 133,175 en AC (2,6635 mg; 266,35 mg/g). Si se redondea al hablar, 187 y 133, o 375 y 266 mg/g, es aceptable siempre que no se presente como un nuevo cálculo."
    )

    pdf.h1("6. Langmuir y PSO sin confundirlos")
    pdf.bullet("Langmuir responde a cuánto cabe en equilibrio (qmax, KL, qe, Ce).")
    pdf.bullet("PSO responde a cómo crecería qt con el tiempo de laboratorio, en minutos.")
    pdf.bullet("GO: qe_PSO = 384,6 mg/g y k2 = 0,0002. AC: 100,4 mg/g y k2 = 0,00910.")
    pdf.bullet("Los pasos de la simulación no son esos minutos. α es un cociente exploratorio, no una constante física.")
    pdf.bullet("Ecuación PSO: qt(t) = (k2 · qe² · t) / (1 + k2 · qe · t).")

    pdf.h1("7. P_ads y S*")
    pdf.p(
        "P_ads = 1 significa: si hay contacto y capacidad, el objeto se adsorbe. Es la regla de la campaña. S* = 0,55 es un sticking probability publicado para otro carbón activo y azul de metileno (Sha'Ato, 2021). No se usó como P_ads. Si preguntan por qué no se puso 0,55: porque igualar ambos símbolos habría convertido una referencia bibliográfica en una ley del motor sin evidencia de que el carbón sea el mismo."
    )

    pdf.h1("8. Qué se comprobó antes de la campaña")
    pdf.bullet("Que alargar los pasos frena el aumento de Nads, sin meseta perfecta.")
    pdf.bullet("Que cambiar la geometría cambia los números; la geometría vieja se archivó, no se borró.")
    pdf.bullet("Que cambiar P_ads modifica la cantidad adsorbida y también puede modificar las trayectorias; en GO, la relación no es monótona en todas las configuraciones.")
    pdf.bullet("Que la masa se conserva y que la misma semilla repite el resultado.")
    pdf.bullet("135 pruebas automáticas en el estado actual del repositorio.")
    pdf.p(
        "Orden útil si preguntan «cómo se llegó aquí»: primero se vio que el horizonte y sigma cambian el resultado; después se alineó la geometría y se archivó la anterior; luego se miró el PSO de cada material sin convertir pasos en minutos; el barrido de P_ads no eligió un valor físico; la campaña de 40+40 se ejecutó con la regla P_ads = 1 y no se volvió a tocar."
    )

    pdf.h1("9. Cómo responder sin pasarse")
    pdf.p("Frases seguras:")
    pdf.bullet("«Es un modelo computacional de objetos, no una medida de laboratorio.»")
    pdf.bullet("«Langmuir y PSO están al lado, no dentro de la regla de adsorción.»")
    pdf.bullet("«Sigma está en píxeles por paso; no se ha demostrado que sea un D experimental.»")
    pdf.bullet("«GO retiene más MB que AC en este protocolo, con poca dispersión entre semillas.»")
    pdf.h2("Frases que conviene no usar")
    pdf.bullet("«Es una simulación molecular» o «así se comporta la molécula de agua».")
    pdf.bullet("«El modelo demuestra que el GO es mejor adsorbente en el laboratorio».")
    pdf.bullet("«2000 pasos son X minutos» o «sigma es el coeficiente de difusión medido».")
    pdf.bullet("«P_ads = 1 porque la probabilidad experimental es 1» o «S* = 0,55 es el P_ads».")
    pdf.bullet("«La corrida está mal porque supera 380,7 mg/g».")

    pdf.h1("10. Diez cosas que hay que saber sí o sí", new_page=True)
    items = [
        "El modelo es 2D y mesoscópico, no molecular.",
        "Ciclo: movimiento, contacto, adsorción, qt.",
        "C0 = 100 mg/L; 4 mg de MB en 40 mL.",
        "200 MB de 0,02 mg; 100 unidades de adsorbente de 0,1 mg.",
        "GO móvil 7×7; AC fijo 2×2; MB 1×1; radios 3,5 / 1,0 / 0,5 px.",
        "Campaña: σ = 1,5, 2000 pasos, P_ads = 1, semillas 1–40.",
        "GO ≈ 187 adsorbidos, 94 %, 375 mg/g. AC ≈ 133, 67 %, 266 mg/g.",
        "Contactos ≠ adsorciones. GO contacta más; AC convierte mejor cada contacto.",
        "Superar el qe de Langmuir en alguna semilla de GO no invalida la corrida.",
        "S* = 0,55 no es el P_ads del modelo. Los pasos no son minutos.",
    ]
    for i, text in enumerate(items, 1):
        pdf.bullet(f"{i}. {text}")

    pdf.h1("11. Preguntas probables", new_page=True)
    qa = [
        (
            "¿Por qué el GO adsorbe más?",
            "En el modelo, el GO se mueve y su radio de contacto es mayor (4,0 px frente a 1,5 px). Hay más encuentros. No se afirma un mecanismo químico.",
        ),
        (
            "¿El resultado valida el experimento?",
            "No. La propia campaña está etiquetada como ejecución computacional, no como validación experimental.",
        ),
        (
            "¿Por qué qt de GO puede pasar de 380,7 mg/g?",
            "Porque la adsorción es por objetos enteros y el motor no está programado para frenar en el qe de Langmuir.",
        ),
        (
            "¿Qué es sigma?",
            "La desviación típica del salto aleatorio, en píxeles por paso. En la campaña vale 1,5.",
        ),
        (
            "¿Se puede pasar la simulación a minutos?",
            "No de forma demostrada. El PSO está en minutos; la simulación, en pasos. α se exploró y no se fijó.",
        ),
        (
            "¿Por qué 40 repeticiones?",
            "Para estimar media y dispersión. El código contemplaba la duda 30 frente a 40; la campaña final usó 40 por material.",
        ),
        (
            "¿La ventana gráfica cambia la ciencia?",
            "No. Avanza con la misma función que el cálculo sin ventana. La misma semilla da las mismas métricas.",
        ),
        (
            "¿Por qué hay más contactos que adsorciones?",
            "Porque un encuentro no siempre deja sitio para otro objeto de 0,02 mg. Con P_ads = 1, cada adsorción es un evento, pero un mismo sólido puede ser tocado muchas veces.",
        ),
        (
            "¿Qué es qmax y qué es qe?",
            "qmax es la capacidad de la isoterma de Langmuir. qe es la cantidad en equilibrio para estas condiciones (380,7 mg/g en GO y 290,9 mg/g en AC). La simulación no está obligada a terminar en qe.",
        ),
        (
            "¿La masa se conserva?",
            "Sí en las 80 corridas finales: adsorbido más libre recupera los 4 mg. Es una comprobación del motor, no una medida de laboratorio.",
        ),
        (
            "¿Qué quedaría por hacer?",
            "Identificar sigma con una escala física, relacionar pasos y minutos, y disponer de un P_ads propio de estos materiales. Nada de eso se inventó para cerrar la campaña.",
        ),
    ]
    for q, a in qa:
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Arial", "B", pdf.body)
        pdf.multi_cell(0, pdf.lead, "P. " + q)
        pdf.set_x(pdf.l_margin)
        pdf.set_font("Arial", "", pdf.body)
        pdf.multi_cell(0, pdf.lead, "R. " + a)
        pdf.ln(1.2)

    pdf.h1("12. Plan de estudio en tres pasadas", new_page=True)
    pdf.h2("Primera pasada: el esquema")
    pdf.p(
        "Leer solo la cadena movimiento → contacto → adsorción → qt, la tabla de condiciones y la tabla de medias. Al terminar hay que poder decir, sin mirar, qué es el modelo y cuáles son los dos números grandes: cerca de 375 mg/g en GO y cerca de 266 mg/g en AC."
    )
    pdf.h2("Segunda pasada: las distinciones")
    pdf.p(
        "Separar cuatro cosas que se confunden con facilidad. Primera: parámetro de condición (temperatura, pH, masas, C0, qmax, KL). Segunda: número derivado (C0 = 4 mg / 0,04 L; qt a partir de Nads). Tercera: decisión de ejecución (sigma, pasos, semilla, P_ads = 1). Cuarta: dibujo (1×1, 7×7, 2×2 px). Si una pregunta mezcla dos clases, la respuesta empieza por decir a cuál pertenece."
    )
    pdf.p(
        "En la misma pasada: Langmuir es equilibrio de referencia; PSO es una curva en minutos de laboratorio; la simulación avanza por pasos. α se calculó para explorar y no se adoptó. S* = 0,55 se leyó y no se copió a P_ads."
    )
    pdf.h2("Tercera pasada: la defensa")
    pdf.p(
        "Recorrer las preguntas del apartado 11 en voz alta. Después, el mapa del apartado 13, en menos de cinco minutos. Si una frase suena a «el experimento demuestra», reescribirla como «en este modelo, bajo este protocolo»."
    )

    pdf.h1("13. Si proyectan una figura")
    pdf.bullet("Puntos por semilla: «cada punto es una repetición independiente, no un instante».")
    pdf.bullet("Histograma: «GO queda a la derecha de AC; en Nads los rangos no se solapan».")
    pdf.bullet("Línea horizontal de Langmuir: «es la referencia, no el sitio donde el programa debe parar». En GO, el máximo de campaña es 392 mg/g.")
    pdf.bullet("Curva frente a pasos: «el eje no está en minutos». La curva PSO, si aparece, sí está en minutos y es otra figura.")
    pdf.bullet("Eficiencia: «AC convierte mejor cada contacto; GO tiene muchos más contactos. No son la misma magnitud».")

    pdf.h1("14. Mapa breve para una exposición", new_page=True)
    pdf.bullet("Minuto 1. Decir qué es: objetos en un plano, no moléculas. Cadena movimiento, contacto, adsorción, qt.")
    pdf.bullet("Minuto 2. Condiciones: 25 °C, pH 6, 4 mg, 10 mg, 40 mL, C0 = 100 mg/L. Protocolo: sigma 1,5, 2000 pasos, P_ads = 1, 40 semillas.")
    pdf.bullet("Minuto 3. Resultados: GO cerca de 187 objetos y 375 mg/g; AC cerca de 133 objetos y 266 mg/g. GO contacta más; AC convierte mejor cada contacto.")
    pdf.bullet("Minuto 4. Referencias al lado: Langmuir 380,7 y 290,9 mg/g; PSO con curvas distintas y en minutos. Alguna semilla de GO pasa de 380,7 y no se corrige.")
    pdf.bullet("Cierre. Masa conservada, misma semilla repetible, y el resultado no es una validación experimental.")

    pdf.h1("15. Una semilla concreta")
    go, ac = load_campaign()
    g1, a1 = go[1], ac[1]
    pdf.p(
        "La semilla 1 no es la media. Sirve para enseñar que una sola corrida ya trae todas las magnitudes. "
        f"En GO: {g1['n_adsorbed']} objetos adsorbidos, qt = {_num(g1['qfinal_mg_g'], 0)} mg/g, "
        f"{g1['n_contacts']} contactos, eficiencia {_num(g1['contact_to_adsorption_efficiency'], 3)}. "
        f"En AC: {a1['n_adsorbed']} objetos, qt = {_num(a1['qfinal_mg_g'], 0)} mg/g, "
        f"{a1['n_contacts']} contactos, eficiencia {_num(a1['contact_to_adsorption_efficiency'], 3)}. "
        "Misma semilla numérica, materiales distintos, resultados distintos. La media de 40 semillas es la que se cita en la comparación."
    )

    pdf.h1("16. Lista de comprobación antes de exponer", new_page=True)
    for item in [
        "He dicho que el modelo es bidimensional y mesoscópico, no molecular.",
        "He separado contacto geométrico y adsorción.",
        "He dicho C0 = 100 mg/L, no 100 mg/g.",
        "He citado el protocolo: sigma 1,5; 2000 pasos; P_ads = 1; semillas 1 a 40.",
        "He dado las medias aproximadas: 187 y 375 mg/g (GO); 133 y 266 mg/g (AC).",
        "He dicho que GO contacta más y que AC tiene mayor eficiencia de contacto.",
        "He situado Langmuir (380,7 y 290,9) como referencia, no como tope del programa.",
        "He avisado de que alguna semilla de GO llega a 392 mg/g.",
        "He dejado el PSO en minutos y la simulación en pasos.",
        "He distinguido S* = 0,55 de P_ads = 1.",
        "He dicho que la masa cuadra en las 80 corridas y que la misma semilla se repite.",
        "He cerrado con: es una campaña computacional, no una validación experimental.",
    ]:
        pdf.bullet(item)

    pdf.h1("17. Guion corto, ya redactado")
    pdf.p(
        "El trabajo simula, en un plano, la adsorción de azul de metileno sobre óxido de grafeno y sobre carbón activado. No es una simulación molecular. Los objetos se desplazan con saltos aleatorios, se tocan si la distancia es menor o igual que la suma de radios, y el colorante queda asociado al sólido solo si cabe un objeto entero de 0,02 mg."
    )
    pdf.p(
        "Las condiciones de referencia son 25 °C, pH 6, 4 mg de colorante, 10 mg de adsorbente y 40 mL, es decir 100 mg/L. La campaña final usa la geometría de representación MB 1×1, GO 7×7 móvil y AC 2×2 fijo, con sigma 1,5 píxeles por paso, 2000 pasos y la regla P_ads = 1. Hay 40 semillas por material."
    )
    pdf.p(
        "En esas condiciones el GO adsorbe, de media, 187,45 objetos, un 93,73 % y 374,9 mg/g. El AC adsorbe 133,18 objetos, un 66,59 % y 266,35 mg/g. La diferencia es de unos 54 objetos y 109 mg/g. El GO acumula más contactos; el AC convierte en adsorción una fracción mayor de los contactos que tiene. Contacto y adsorción no son lo mismo."
    )
    pdf.p(
        "Langmuir sitúa el equilibrio de referencia en 380,7 mg/g para el GO y 290,9 mg/g para el AC. El programa no está obligado a terminar ahí: alguna semilla de GO llega a 392 mg/g. El PSO es otra referencia, en minutos, y cada material tiene la suya. Los pasos de la simulación no se han convertido en esos minutos. S* = 0,55 es una cifra bibliográfica de otro carbón y no es el P_ads de la campaña. La masa se conserva en las 80 corridas. El resultado describe el modelo; no valida un experimento."
    )

    pdf.h1("18. Resumen para memorizar", new_page=True)
    pdf.p(
        "Objetos en un cuadrado. Saltan con sigma = 1,5. Si se tocan y cabe 0,02 mg, el MB queda adsorbido (P_ads = 1). A los 2000 pasos y con 40 semillas, el GO retiene unos 187 objetos (qt cerca de 375 mg/g) y el AC unos 133 (qt cerca de 266 mg/g). Langmuir y el PSO se miran al lado. La masa cuadra. No es un experimento."
    )
    pdf.bullet("No es dinámica molecular ni un ensayo de laboratorio.")
    pdf.bullet("Contacto geométrico no equivale a partícula adsorbida.")
    pdf.bullet("P_ads = 1 es la regla de la campaña. S* = 0,55 no la sustituye.")
    pdf.bullet("Los pasos no se han demostrado equivalentes a minutos.")
    pdf.bullet("Superar 380,7 mg/g en alguna semilla de GO no invalida la corrida.")
    return pdf


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    memory = build_memory()
    guide = build_guide()
    mpath = DOCS / "documentacion_cientifica_tecnica_GO_AC.pdf"
    gpath = DOCS / "guia_estudio_simulacion_GO_AC.pdf"
    memory.output(str(mpath))
    guide.output(str(gpath))
    print(f"memoria_paginas={memory.page_no()} path={mpath}")
    print(f"guia_paginas={guide.page_no()} path={gpath}")


if __name__ == "__main__":
    main()
