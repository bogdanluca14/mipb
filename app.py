import sys
import subprocess

def ensure_package(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

ensure_package('streamlit')
ensure_package('folium')
ensure_package('requests')

import streamlit as st
import folium
from streamlit.components.v1 import html
import random
import requests

st.set_page_config(page_title="Mentor Carieră AI", page_icon="🎓", layout="wide")

hide_streamlit_style = """
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

st.markdown("# 🎓 Mentor Carieră AI")
st.markdown("_Completează formularul, alege domeniul, apoi apasă **Vezi recomandări AI**_")

subjects_list = ["Matematică", "Informatică", "Fizică", "Chimie", "Biologie",
                 "Limba și literatura română", "Istorie", "Geografie",
                 "Economie", "Arte"]

careers_list = ["Programator", "Medic", "Inginer", "Profesor", "Cercetător", "Militar",
                "Artist", "Muzician", "Jurist", "Jurnalist", "Economist", "Polițist",
                "Antreprenor", "Psiholog", "Veterinar", "Arhitect", "Farmacist",
                "Contabil", "Scriitor", "Designer", "Analist de date", "Politician"]

career_data = {
    "Programator": {
        "subjects": ["Matematică", "Informatică", "Fizică"],
        "mode": "Individual",
        "creativity": "med",
        "people": "low",
        "reason": "ai înclinație pentru logică și informatică",
        "steps": [
            "Învață bazele programării (ex: Python) prin cursuri online",
            "Realizează proiecte personale pentru portofoliu",
            "Aplică la internship-uri în dezvoltare software"
        ],
        "title": "Programator junior"
    },
    "Medic": {
        "subjects": ["Biologie", "Chimie"],
        "mode": "Team",
        "creativity": "med",
        "people": "high",
        "reason": "îți pasă de oameni și ești atras de științele vieții",
        "steps": [
            "Învață serios la biologie și chimie pentru admiterea la medicină",
            "Intră la o facultate de medicină și farmacie (6 ani de studiu)",
            "Urmează rezidențiatul într-o specializare medicală aleasă"
        ],
        "title": "Medic"
    },
    "Inginer": {
        "subjects": ["Matematică", "Fizică", "Informatică"],
        "mode": "Both",
        "creativity": "med",
        "people": "low",
        "reason": "ești orientat spre soluții practice și stăpânești științele exacte",
        "steps": [
            "Consolidează-ți cunoștințele de matematică și fizică prin proiecte practice",
            "Intră la o universitate tehnică (Politehnică) într-un domeniu de inginerie",
            "Participă la stagii sau proiecte de inginerie pentru experiență practică"
        ],
        "title": "Inginer"
    },
    "Profesor": {
        "subjects": ["Limba și literatura română", "Istorie", "Geografie"],
        "mode": "Both",
        "creativity": "med",
        "people": "high",
        "reason": "îți place să împărtășești cunoștințe și ai răbdare cu ceilalți",
        "steps": [
            "Studiază disciplina pe care vrei să o predai la o facultate de profil",
            "Urmează modulul pedagogic pentru a dobândi competențe didactice",
            "Fă practică într-o școală și implică-te în proiecte educative"
        ],
        "title": "Profesor"
    },
    "Cercetător": {
        "subjects": ["Biologie", "Chimie", "Fizică", "Informatică"],
        "mode": "Both",
        "creativity": "high",
        "people": "low",
        "reason": "ești curios din fire și pasionat de a descoperi lucruri noi",
        "steps": [
            "Urmează o facultate și apoi un program de masterat în domeniul care te pasionează",
            "Implică-te în proiecte de cercetare încă din timpul facultății",
            "Continuă cu un program de doctorat și publică rezultate în jurnale științifice"
        ],
        "title": "Cercetător"
    },
    "Artist": {
        "subjects": ["Arte"],
        "mode": "Individual",
        "creativity": "high",
        "people": "low",
        "reason": "ai talent creativ și dorința de a te exprima prin artă",
        "steps": [
            "Perfecționează-ți abilitățile artistice realizând un portofoliu de lucrări",
            "Urmează o facultate sau cursuri de artă pentru a-ți îmbunătăți tehnica",
            "Expune-ți creațiile în galerii sau online pentru a-ți face cunoscut talentul"
        ],
        "title": "Artist"
    },
    "Muzician": {
        "subjects": ["Arte"],
        "mode": "Both",
        "creativity": "high",
        "people": "low",
        "reason": "ai talent muzical și creativitate artistică",
        "steps": [
            "Studiază intens un instrument sau canto, sub îndrumarea unui profesor",
            "Urmează o facultate de muzică sau cursuri avansate de specialitate",
            "Participă la concursuri și concerte pentru a-ți lansa cariera muzicală"
        ],
        "title": "Muzician"
    },
    "Jurist": {
        "subjects": ["Istorie", "Limba și literatura română"],
        "mode": "Individual",
        "creativity": "med",
        "people": "med",
        "reason": "ai abilități de comunicare și te preocupă dreptatea",
        "steps": [
            "Pregătește-te la discipline socio-umane (istorie, română) pentru admiterea la drept",
            "Finalizează studiile la o facultate de drept (4 ani) și efectuează stagiul (INM sau barou) pentru calificare",
            "Câștigă experiență lucrând într-un birou de avocatura sau prin internship-uri în domeniul juridic"
        ],
        "title": "Jurist"
    },
    "Polițist": {
        "subjects": ["Istorie", "Limba și literatura română"],
        "mode": "Individual",
        "creativity": "med",
        "people": "med",
        "reason": "te preocupă dreptatea și ai abilități de comunicare",
        "steps": [
            "Pregătește-te fizic și învață o limbă de circulație internațională",
            "Pregătește-te la discipline socio-umane (istorie, română) pentru admiterea la o școală de poliție",
            "Finalizează studiile la academia de poliție (4 ani) sau la o școală de agenți de poliție"
        ],
        "title": "Polițist"
    },
    "Militar": {
        "subjects": ["Matematică", "Fizică"],
        "mode": "Both",
        "creativity": "med",
        "people": "med",
        "reason": "ești orientat spre soluții practice și stăpânești științele exacte",
        "steps": [
            "Pregătește-te fizic și învață o limbă de circulație internațională",
            "Consolidează-ți cunoștințele de matematică și fizică prin proiecte practice",
            "Finalizează studiile la o academie militară"
        ],
        "title": "Militar"
    },
    "Jurnalist": {
        "subjects": ["Limba și literatura română", "Istorie", "Geografie"],
        "mode": "Both",
        "creativity": "high",
        "people": "med",
        "reason": "ești curios și ai talent la scris, dorind să informezi oamenii",
        "steps": [
            "Implică-te la revista școlii sau creează un blog pentru a exersa scrisul și documentarea",
            "Urmează o facultate de jurnalism sau comunicare pentru formare profesională",
            "Fă un stagiu într-o redacție locală sau la un post media pentru a dobândi experiență practică"
        ],
        "title": "Jurnalist"
    },
    "Economist": {
        "subjects": ["Matematică", "Economie"],
        "mode": "Individual",
        "creativity": "low",
        "people": "low",
        "reason": "ai gândire analitică și interes pentru afaceri și economie",
        "steps": [
            "Aprovizionează-te cu noțiuni de bază de economie și finanțe încă din liceu",
            "Urmează Academia de Studii Economice sau o facultate de profil economic",
            "Participă la internship-uri într-o bancă sau companie pentru a înțelege practic domeniul financiar"
        ],
        "title": "Economist"
    },
    "Antreprenor": {
        "subjects": ["Economie", "Informatică"],
        "mode": "Both",
        "creativity": "high",
        "people": "med",
        "reason": "îți asumi riscuri și ai viziune pentru a începe proiecte noi",
        "steps": [
            "Pornește un proiect mic sau o afacere pe cont propriu, chiar și experimental, pentru a învăța",
            "Caută mentori și programe de antreprenoriat (workshop-uri, incubatoare) de la care să obții îndrumare",
            "Fii perseverent: învață din eșecuri și îmbunătățește-ți constant ideile de afaceri"
        ],
        "title": "Antreprenor"
    },
    "Psiholog": {
        "subjects": ["Biologie", "Limba și literatura română"],
        "mode": "Individual",
        "creativity": "med",
        "people": "high",
        "reason": "ai empatie și ești interesat de mintea umană",
        "steps": [
            "Citește despre psihologie și încearcă să înțelegi comportamentul uman",
            "Urmează o facultate de psihologie și profită de practică pentru a-ți forma abilitățile",
            "Participă ca voluntar în proiecte de consiliere sau centre de suport pentru a câștiga experiență cu oamenii"
        ],
        "title": "Psiholog"
    },
    "Veterinar": {
        "subjects": ["Biologie", "Chimie"],
        "mode": "Both",
        "creativity": "low",
        "people": "high",
        "reason": "iubești animalele și ai cunoștințe de biologie",
        "steps": [
            "Fă voluntariat la un cabinet veterinar sau adăpost de animale pentru a căpăta experiență",
            "Urmează Facultatea de Medicină Veterinară (parte din universitățile de științe agricole și medicină veterinară)",
            "Specializează-te într-un domeniu (animale de companie, animale mari etc.) și obține licența de liberă practică"
        ],
        "title": "Medic veterinar"
    },
    "Arhitect": {
        "subjects": ["Matematică", "Arte"],
        "mode": "Both",
        "creativity": "high",
        "people": "med",
        "reason": "ai simț estetic și gândire spațială, combinând arta cu știința",
        "steps": [
            "Exersează desenul tehnic și proiectarea (poți urma cursuri de arhitectură pentru liceeni)",
            "Intră la o universitate de arhitectură (ex: „Ion Mincu” București) și finalizează studiile de licență și master",
            "Alătură-te unui birou de arhitectură ca stagiar pentru a învăța practic și obține drept de semnătură ca arhitect"
        ],
        "title": "Arhitect"
    },
    "Farmacist": {
        "subjects": ["Chimie", "Biologie"],
        "mode": "Individual",
        "creativity": "low",
        "people": "med",
        "reason": "ești atent la detalii și pasionat de chimie și sănătate",
        "steps": [
            "Pregătește-te la chimie pentru admiterea la facultatea de farmacie",
            "Urmează Facultatea de Farmacie (5 ani) pentru a deveni licențiat în farmacie",
            "Câștigă experiență lucrând într-o farmacie ca intern, apoi ca farmacist cu drept de liberă practică"
        ],
        "title": "Farmacist"
    },
    "Contabil": {
        "subjects": ["Matematică", "Economie"],
        "mode": "Individual",
        "creativity": "low",
        "people": "low",
        "reason": "ești organizat, atent la detalii și te descurci bine cu cifrele",
        "steps": [
            "Participă la un curs de contabilitate primară încă din liceu, dacă este posibil",
            "Urmează o facultate de contabilitate și informatică de gestiune sau un profil economic similar",
            "Obține o certificare profesională (ex: CECCAR) și caută un post de contabil junior pentru a acumula experiență"
        ],
        "title": "Contabil"
    },
    "Scriitor": {
        "subjects": ["Limba și literatura română", "Istorie", "Arte"],
        "mode": "Individual",
        "creativity": "high",
        "people": "low",
        "reason": "ai imaginație bogată și talent de a comunica idei în scris",
        "steps": [
            "Scrie constant – povestiri, poezii, articole – pentru a-ți dezvolta stilul",
            "Citește literatură variată pentru a-ți lărgi orizontul și a învăța de la autori consacrați",
            "Înscrie-te la concursuri literare sau ateliere de scriere creativă și încearcă să-ți publici lucrările"
        ],
        "title": "Scriitor"
    },
    "Designer": {
        "subjects": ["Arte", "Informatică"],
        "mode": "Individual",
        "creativity": "high",
        "people": "low",
        "reason": "ai ochi pentru estetică și creativitate în a realiza concepte vizuale",
        "steps": [
            "Învață instrumente de design grafic (ex: Photoshop, Illustrator) sau tehnici de design vestimentar, în funcție de domeniul ales",
            "Construiește-ți un portofoliu cu proiecte proprii pentru a-ți demonstra abilitățile",
            "Aplică la internship-uri sau joburi junior de designer pentru a obține experiență practică și a învăța din industrie"
        ],
        "title": "Designer"
    },
    "Analist de date": {
        "subjects": ["Matematică", "Informatică"],
        "mode": "Individual",
        "creativity": "med",
        "people": "low",
        "reason": "îți plac cifrele și identificarea tiparelor ascunse în date",
        "steps": [
            "Dezvoltă-ți cunoștințele de statistică și programare (ex: Python, R) prin cursuri online",
            "Urmează o specializare în data science sau informatică la facultate sau master",
            "Aplică abilitățile pe seturi de date reale (proiecte practice) și caută un internship ca analist de date"
        ],
        "title": "Analist de date"
    },
    "Politician": {
        "subjects": ["Istorie", "Geografie", "Limba și literatura română"],
        "mode": "Team",
        "creativity": "med",
        "people": "high",
        "reason": "îți dorești să contribui la societate și ai abilități de lider",
        "steps": [
            "Implică-te în consiliul elevilor sau în proiecte comunitare, ca să capeți experiență de leadership",
            "Studiază științe politice, administrație publică sau drept ca să înțelegi sistemul de guvernare",
            "Alătură-te unei organizații de tineret (de exemplu, unui partid politic) și construiește-ți rețeaua în domeniu"
        ],
        "title": "Politician"
    }
}

career_top_faculties = {
    "Programator": [
        {
            "name": "Universitatea Politehnica din București",
            "rank": "(QS Ranking) #1 Computer Science în România",
            "url": "https://www.upb.ro",
            "img": "https://acs.pub.ro/public/poster_acs_cover4-1024x715.jpg",
            "lat": 44.43833,
            "lon": 26.05139,
            "desc": "Cea mai prestigioasă universitate tehnică, cu programe solide de informatică și inginerie software."
        },
        {
            "name": "Universitatea Tehnică din Cluj-Napoca",
            "rank": "Top 2 CS în România",
            "url": "https://www.utcluj.ro",
            "img": "https://www.stiridecluj.ro/files/thumbs/259/7f5b4b6b8669164c4799fc52a86fd3f0.jpeg",
            "lat": 46.76920,
            "lon": 23.58550,
            "desc": "Renumită pentru centrele de cercetare în informatică și colaborările internaționale în software engineering."
        },
        {
            "name": "Universitatea din București",
            "rank": "Top 3 CS în România",
            "url": "https://unibuc.ro",
            "img": "https://img.a1.ro/?u=https%3A%2F%2Fa1.ro%2Fuploads%2Fmodules%2Fnews%2F0%2F2018%2F7%2F8%2F781881%2F1531058737d55e5112.jpg?w=1200&h=630&c=1",
            "lat": 44.43556,
            "lon": 26.10112,
            "desc": "Facultatea de Matematică și Informatică oferă cursuri avansate și proiecte de AI și Big Data."
        }
    ],
    "Medic": [
        {
            "name": "Universitatea de Medicină și Farmacie \"Carol Davila\" București",
            "rank": "#1 Medicină în România",
            "url": "https://umfcd.ro",
            "img": "https://umfcd.ro/wp-content/uploads/2018/10/743407-1532605235-listele-complete-cu-rezultatele-de-la-admiterea-la-medicina-bucuresti.jpg",
            "lat": 44.43528,
            "lon": 26.07000,
            "desc": "Una dintre cele mai vechi și prestigioase facultăți medicale, cu programe clinice extinse."
        },
        {
            "name": "Universitatea de Medicină și Farmacie Iuliu Hațieganu Cluj-Napoca",
            "rank": "Top 2 Medicină în România",
            "url": "https://www.umfcluj.ro",
            "img": "https://cdn.umfcluj.ro/uploads/2021/10/umfih-07.jpg",
            "lat": 46.76206,
            "lon": 23.58360,
            "desc": "Cunoscută pentru cercetare biomedicală și parteneriate cu spitale universitare de top."
        },
        {
            "name": "Universitatea de Medicină și Farmacie Grigore T. Popa Iași",
            "rank": "Top 3 Medicină în România",
            "url": "https://www.umfiasi.ro",
            "img": "https://news.umfiasi.ro/wp-content/uploads/2023/01/umf-iasi.jpg",
            "lat": 47.16015,
            "lon": 27.59581,
            "desc": "Pionier în educație medicală în Moldova, cu programe solide de cercetare clinică."
        }
    ],
    "Inginer": [
        {
            "name": "Universitatea Politehnica din București",
            "rank": "(QS Ranking) #1 Inginerie în România",
            "url": "https://www.upb.ro",
            "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcShu1KuSt9PuPhRBa0QO55ViyzNxMvCcX2U0g&s",
            "lat": 44.43833,
            "lon": 26.05139,
            "desc": "Lider în inginerie mecanică, electrotehnică și IT, cu laboratoare de ultimă generație."
        },
        {
            "name": "Universitatea Politehnica Timișoara",
            "rank": "Top 2 Inginerie în România",
            "url": "https://www.upt.ro",
            "img": "https://upt.ro/img/51445rectorat-upt-1.jpg",
            "lat": 45.75396,
            "lon": 21.22561,
            "desc": "Programe tehnice, proiecte Erasmus și cooperare cu industria europeană."
        },
        {
            "name": "Universitatea Tehnică din Cluj-Napoca",
            "rank": "Top 3 Inginerie în România",
            "url": "https://www.utcluj.ro",
            "img": "https://ie.utcluj.ro/files/Acasa/images/Facultatea2.jpg",
            "lat": 46.76920,
            "lon": 23.58550,
            "desc": "Renumită pentru departamentele de inginerie civilă și energetică."
        }
    ],
    "Profesor": [
        {
            "name": "Universitatea din București",
            "rank": "Top 1 Pedagogie în România",
            "url": "https://unibuc.ro",
            "img": "https://fpse.unibuc.ro/wp-content/uploads/2023/01/12094730_1482304882073084_3162350211045692050_o-624x243.jpg",
            "lat": 44.43556,
            "lon": 26.10112,
            "desc": "Facultatea de Psihologie și Științele Educației oferă formare pedagogică avansată."
        },
        {
            "name": "Universitatea Babeș-Bolyai Cluj-Napoca",
            "rank": "Top 2 Pedagogie în România",
            "url": "https://www.ubbcluj.ro",
            "img": "https://hartasanatatiimintale.ro/wp-content/uploads/2024/07/BCU.jpg",
            "lat": 46.76767,
            "lon": 23.59137,
            "desc": "Departament dedicat formării profesorilor, metodologii inovative de predare."
        },
        {
            "name": "Universitatea de Vest Timișoara",
            "rank": "Top 3 Pedagogie în România",
            "url": "https://www.uvt.ro",
            "img": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTKVsCJMr_0mo_FUAxiYX9tBgmFf5orFhhGWg&s",
            "lat": 45.74712,
            "lon": 21.23151,
            "desc": "Facultatea de Sociologie și Psihologie pregătește cadre didactice cu accent pe psihopedagogie."
        }
    ],
    "Cercetător": [
        {
            "name": "Universitatea Babeș-Bolyai Cluj-Napoca",
            "rank": "Top 1 cercetare universitara în România",
            "url": "https://www.ubbcluj.ro",
            "img": "https://visitcluj.ro/wp-content/uploads/2021/05/Universitatea-Babes-Bolyai-UBB-PMC16604_.jpg",
            "lat": 46.76767,
            "lon": 23.59137,
            "desc": "Puternic în STEM, cu peste 200 de proiecte internaționale de cercetare."
        },
        {
            "name": "Universitatea din București",
            "rank": "Top 2 cercetare în România",
            "url": "https://unibuc.ro",
            "img": "https://unibuc.ro/wp-content/uploads/2020/01/shutterstock_576068437-700x480.jpg",
            "lat": 44.43556,
            "lon": 26.10112,
            "desc": "Excelență în științe sociale și natură, centre de cercetare multidisciplinare."
        },
        {
            "name": "Universitatea Alexandru Ioan Cuza Iași",
            "rank": "Top 3 cercetare în România",
            "url": "https://www.uaic.ro",
            "img": "https://iassium.ro/wp-content/uploads/2019/07/iassium-unviersitatea-cuza-iasi.jpg",
            "lat": 47.16222,
            "lon": 27.58889,
            "desc": "Centre de cercetare în științe umaniste, chimie și biologie."
        }
    ],
    "Militar": [
        {
            "name": "Academia Tehnică Militară Ferdinand I",
            "rank": "Top 1 academie militară în România",
            "url": "https://mta.ro/",
            "img": "https://upload.wikimedia.org/wikipedia/ro/5/5f/Academia_Tehnic%C4%83_Militar%C4%83-2.JPG",
            "lat": 46.76767,
            "lon": 23.59137,
            "desc": "Cea mai bună academie militară din România."
        },
        {
            "name": "Școala Militară de Maiștri Militari a Forțelor Navale Amiral Ion Murgescu",
            "rank": "Top 2 școli militare",
            "url": "https://www.smmmfn.ro/",
            "img": "https://ziarulamprenta.ro/wp-content/uploads/2018/11/scoala-maistri-militari.jpg",
            "lat": 44.43556,
            "lon": 26.10112,
            "desc": "Cea mai buna școală militară din România."
        },
        {
            "name": "Şcoala Militară De Maiştri Şi Subofiţeri a Forţelor Terestre Basarab I",
            "rank": "Top 3 școli militare",
            "url": "http://www.ncoacademy.ro/",
            "img": "https://epitesti.ro/wp-content/uploads/2024/10/scoala-de-ofiteri.jpg",
            "lat": 47.16222,
            "lon": 27.58889,
            "desc": "Școală militară destinată forțelor terestre."
        }
    ],
    "Polițist": [
        {
            "name": "Academia de Poliție Alexandru Ioan Cuza",
            "rank": "Top 1 academie de poliție în România",
            "url": "https://academiadepolitie.ro/",
            "img": "https://academiadepolitie.ro/storage/2021/11/cladire_academiadepolitie_outside-700x660.jpg",
            "lat": 46.76767,
            "lon": 23.59137,
            "desc": "Cea mai bună academie de poliție din România."
        },
        {
            "name": "Școala de Agenți de Poliție Vasile Lascăr Câmpina",
            "rank": "Top 2 școli de poliție",
            "url": "https://www.scoalapolitie.ro/",
            "img": "https://gazarul.ro/wp-content/uploads/2024/04/scoala-agenti.jpg",
            "lat": 44.43556,
            "lon": 26.10112,
            "desc": "Cea mai buna școală de poliție din România."
        },
        {
            "name": "Şcoala de Agenţi de poliţie Septimiu Mureşan",
            "rank": "Top 3 școli de poliție",
            "url": "https://www.scoalapolcj.ro/",
            "img": "https://politiaromana.ro/files/pages/big_scoala_cluj1.jpg",
            "lat": 47.16222,
            "lon": 27.58889,
            "desc": "Școala de poliție situată în Cluj-Napoca."
        }
    ],
    "Artist": [
        {
            "name": "Universitatea Națională de Arte București",
            "rank": "Top 1 Arte Vizuale în România",
            "url": "https://unarte.org",
            "img": "https://unarte.org/wp-content/uploads/2021/03/B994699C-F9A0-4D41-ABAE-0952AA42BB39.jpeg",
            "lat": 44.44720,
            "lon": 26.09830,
            "desc": "Centrul principal de formare artistică, programe de licență și masterat diverse."
        },
        {
            "name": "Universitatea de Artă și Design Cluj-Napoca",
            "rank": "Top 2 Arte Vizuale în România",
            "url": "https://uad.ro",
            "img": "https://upload.wikimedia.org/wikipedia/commons/e/e8/Kolozsvar_Matyas_kiraly_szulohaza.JPG",
            "lat": 46.76960,
            "lon": 23.58300,
            "desc": "Renume pentru design grafic, arte plastice și arte decorative."
        },
        {
            "name": "Universitatea de Vest Timișoara - Facultatea de Arte și Design",
            "rank": "Top 3 Arte Vizuale în România",
            "url": "https://www.uvt.ro",
            "img": "https://admitere.uvt.ro/wp-content/uploads/listing-uploads/cover/2022/05/08b.jpg",
            "lat": 45.74712,
            "lon": 21.23151,
            "desc": "Programe interdisciplinare de arte vizuale, design și multimedia."
        }
    ],
    "Muzician": [
        {
            "name": "Universitatea Națională de Muzică București",
            "rank": "Top 1 Muzică în România",
            "url": "https://www.unmb.ro",
            "img": "https://www.societateamuzicala.ro/societateaculturala/wp-content/uploads/2015/04/Universitatea-Nationala-de-Muzica-Bucuresti.jpg",
            "lat": 44.43918,
            "lon": 26.09700,
            "desc": "Lider în educație muzicală, studii superioare de interpretare și compoziție."
        },
        {
            "name": "Universitatea de Vest Timișoara - Facultatea de Muzică și Teatru",
            "rank": "Top 2 Muzică în România",
            "url": "https://www.uvt.ro",
            "img": "https://uvt.ro/wp-content/uploads/2021/01/fmtuvt.jpg",
            "lat": 45.74712,
            "lon": 21.23151,
            "desc": "Programe dedicate interpretării muzicale."
        },
        {
            "name": "Universitatea Babeș-Bolyai Cluj-Napoca - Facultatea de Muzică și Teatru",
            "rank": "Top 3 Muzică în România",
            "url": "https://www.ubbcluj.ro",
            "img": "https://www.ubbcluj.ro/images/thumb_section_structura_1.png",
            "lat": 46.76767,
            "lon": 23.59137,
            "desc": "Renumită pentru programe de muzică clasică și modernă, colaborări internaționale."
        }
    ],
    "Jurist": [
        {
            "name": "Universitatea din București - Facultatea de Drept",
            "rank": "Top 1 Drept în România",
            "url": "https://www.unibuc.ro",
            "img": "https://rrpb.ro/wp-content/uploads/2021/02/facultate-746x400-1.jpg",
            "lat": 44.43556,
            "lon": 26.10112,
            "desc": "Renumită pentru programele de licență și master în drept penal, civil."
        },
        {
            "name": "Academia de Studii Economice București - Facultatea de Drept",
            "rank": "Top 2 Drept în România",
            "url": "https://www.ase.ro",
            "img": "https://tb.ziareromania.ro/Facultatea-de-Drept--introdusa-din-acest-an-de-Academia-de-Studii-Economice-din-Bucuresti--Admiterea-o-sa-fie-online/a35a9562f8e70ca4dd/400/225/2/100/Facultatea-de-Drept--introdusa-din-acest-an-de-Academia-de-Studii-Economice-din-Bucuresti--Admiterea-o-sa-fie-online.jpg",
            "lat": 44.44750,
            "lon": 26.09670,
            "desc": "Programe integrate de drept și economie, focus pe legislație comercială."
        },
        {
            "name": "Universitatea Babeș-Bolyai Cluj-Napoca - Facultatea de Drept",
            "rank": "Top 3 Drept în România",
            "url": "https://www.ubbcluj.ro",
            "img": "https://cdn.g4media.ro/wp-content/uploads/2025/04/fac-de-drept-768x432.jpg",
            "lat": 46.76767,
            "lon": 23.59137,
            "desc": "Curriculum axat pe drept european și dreptul omului."
        }
    ],
    "Jurnalist": [
        {
            "name": "SNSPA - Facultatea de Comunicare și Relații Publice",
            "rank": "Top 1 Jurnalism în România",
            "url": "https://snspa.ro",
            "img": "https://admitere.snspa.ro/wp-content/uploads/2017/02/TUD_1608.jpg",
            "lat": 44.42800,
            "lon": 26.09000,
            "desc": "Program axat pe jurnalism multimedia și comunicare strategică."
        },
        {
            "name": "Universitatea din București - Facultatea de Jurnalism și Științele Comunicării",
            "rank": "Top 2 Jurnalism în România",
            "url": "https://unibuc.ro",
            "img": "https://admitere.unibuc.ro/wp-content/uploads/2023/05/zpd-fjsc-admitere-2023.jpg",
            "lat": 44.43556,
            "lon": 26.10112,
            "desc": "Specializări în jurnalism de investigație și media digitală."
        },
        {
            "name": "Universitatea Babeș-Bolyai Cluj-Napoca - Jurnalism",
            "rank": "Top 3 Jurnalism în România",
            "url": "https://www.ubbcluj.ro",
            "img": "https://www.stiridecluj.ro/files/thumbs/247/c_1ca3f25bef7995d599221eb52736cb3a.png",
            "lat": 46.76767,
            "lon": 23.59137,
            "desc": "Programe în jurnalism cultural și politic cu stagiaturi în mass-media locală."
        }
    ],
    "Economist": [
        {
            "name": "Academia de Studii Economice București",
            "rank": "Top 1 Economie în România",
            "url": "https://www.ase.ro",
            "img": "https://s.iw.ro/gateway/g/ZmlsZVNvdXJjZT1odHRwJTNBJTJGJTJG/c3RvcmFnZWRpZ2lmbTEucmNzLXJkcy5y/byUyRnN0b3JhZ2UlMkYyMDE5JTJGMDUl/MkYyMCUyRjEwNzU0MjlfMTA3NTQyOV9B/U0UtQWNhZGVtaWEtZGUtU3R1ZGlpLUVj/b25vbWljZS5qcGcmdz03ODAmaD00NDAm/aGFzaD03MGFkOGFhZmE4YTI5ODViOWE0Y2FjZGM4NmQyNWM1ZQ==.thumb.jpg",
            "lat": 44.44750,
            "lon": 26.09670,
            "desc": "Lider în științe economice, programe de finanțe, marketing și economie digitală."
        },
        {
            "name": "Universitatea Babeș-Bolyai Cluj-Napoca - Economie și Business",
            "rank": "Top 2 Economie în România",
            "url": "https://www.ubbcluj.ro",
            "img": "https://i0.wp.com/cluju.ro/wp-content/uploads/2017/07/FSEGA-Admitere-Iulie-2017-P10.jpg",
            "lat": 46.76767,
            "lon": 23.59137,
            "desc": "Departament cu cercetare puternică în economie comportamentală și data analytics."
        },
        {
            "name": "Universitatea Alexandru Ioan Cuza Iași - Economie",
            "rank": "Top 3 Economie în România",
            "url": "https://www.uaic.ro",
            "img": "https://www.feaa.uaic.ro/wp-content/uploads/2023/05/FEAA-Corp-B.jpg",
            "lat": 47.16222,
            "lon": 27.58889,
            "desc": "Programe de macroeconomie și politici economice, centre de analize economice."
        }
    ],
    "Politician": [
        {
            "name": "Școala Naţională de Studii Politice și Administrative",
            "rank": "Top 1 Facultăți de Studii Politice în România",
            "url": "https://snspa.ro/",
            "img": "https://studyinromania.gov.ro/resource-c-1078-1200x720-iwh-cladire-snspa-5.jpg",
            "lat": 44.44750,
            "lon": 26.09670,
            "desc": "Lider în studii politice și administrative."
        },
        {
            "name": "Facultatea de Științe Politice, Administrative și ale Comunicării",
            "rank": "Top 2 Facultăți de Științe Politice în România",
            "url": "https://www.ubbcluj.ro",
            "img": "https://www.clujazi.ro/wp-content/uploads/FSPAC.jpg",
            "lat": 46.76767,
            "lon": 23.59137,
            "desc": "Facultate de științe politice și administrative, situată în Cluj."
        }
    ],
    "Antreprenor": [
        {
            "name": "Academia de Studii Economice București",
            "rank": "#1 Științe Economice în România",
            "url": "https://www.esb-business-school.de/en/the-esb/partner-universities/detailsite/bucharest-university-of-economic-studies",
            "img": "https://tb.ziareromania.ro/Te-pregatesti-sa-devii-student--Alege-Academia-de-Studii-Economice-din-Bucuresti-/049d556023050afc7a/400/225/2/100/Te-pregatesti-sa-devii-student--Alege-Academia-de-Studii-Economice-din-Bucuresti-.jpg",
            "lat": 44.44750,
            "lon": 26.09670,
            "desc": "Una dintre cele mai mari și specializate universități de economie și business, cu centre pentru startup-uri și cursuri dedicate antreprenoriatului."
        },
        {
            "name": "Universitatea Babeș-Bolyai Cluj-Napoca - Facultatea de Științe Economice și Gestiunea Afacerilor",
            "rank": "Locul 2 în Business & Management în România",
            "url": "https://www.ubbcluj.ro/despre/facultati/fsega/",
            "img": "https://www.ubbcluj.ro/images/picture_istoric_fsega_.jpg",
            "lat": 46.76767,
            "lon": 23.59137,
            "desc": "Renumită pentru curriculele de business moderne, laboratoare de simulare și competiții de antreprenoriat."
        },
        {
            "name": "Universitatea Alexandru Ioan Cuza Iași - Facultatea de Economie și Administrarea Afacerilor",
            "rank": "Locul 3 în Științe Economice în România",
            "url": "https://www.feaa.uaic.ro",
            "img": "https://www.feaa.uaic.ro/wp-content/uploads/2023/05/FEAA-Corp-B.jpg",
            "lat": 47.16222,
            "lon": 27.58889,
            "desc": "Cunoscută pentru cercetarea în macroeconomie și politici economice, conferințe internaționale și proiecte de colaborare cu instituții europene."
        }
    ],
    "Psiholog": [
        {
            "name": "Universitatea din București Facultatea de Psihologie și Științele Educației",
            "rank": "Top 1 Psihologie în România",
            "url": "https://fpse.unibuc.ro",
            "img": "https://fpse.unibuc.ro/wp-content/uploads/2023/01/12094730_1482304882073084_3162350211045692050_o-624x243.jpg",
            "lat": 44.43556,
            "lon": 26.10112,
            "desc": "Formare pedagogică și psihopedagogie, psihologie clinică și organizațională."
        },
        {
            "name": "Universitatea Babeș-Bolyai Cluj-Napoca Facultatea de Psihologie și Științele Educației",
            "rank": "Top 2 Psihologie în România",
            "url": "https://www.ubbcluj.ro",
            "img": "https://psiedu.ubbcluj.ro/data/uploads/poze/biblioteca.jpg",
            "lat": 46.76767,
            "lon": 23.59137,
            "desc": "Programe de consiliere psihologică, psihologie socială și educațională."
        },
        {
            "name": "Universitatea de Vest Timișoara Facultatea de Sociologie și Psihologie",
            "rank": "Top 3 Psihologie în România",
            "url": "https://www.uvt.ro",
            "img": "https://www.timisoreni.ro/upload/photo/2012-03/universitatea_de_vest_timisoara_2_large.jpg",
            "lat": 45.74712,
            "lon": 21.23151,
            "desc": "Psihologie clinică, organizațională și educațională, centre de practică pentru studenți."
        }
    ],
    "Veterinar": [
        {
            "name": "Universitatea de Științe Agricole și Medicină Veterinară Cluj-Napoca",
            "rank": "Top 1 Medicină Veterinară în România",
            "url": "https://www.usamvcluj.ro",
            "img": "https://i0.wp.com/cluju.ro/wp-content/uploads/2022/05/USAMV-Cluj.jpg",
            "lat": 46.76670,
            "lon": 23.56670,
            "desc": "Pionier în educație veterinară, centre de cercetare și clinici veterinare universitare."
        },
        {
            "name": "Universitatea de Științe Agricole și Medicină Veterinară București (USAMV)",
            "rank": "Top 2 Medicină Veterinară în România",
            "url": "https://www.usamv.ro",
            "img": "https://usamv.ro/wp-content/uploads/2022/11/univ.jpg",
            "lat": 44.43930,
            "lon": 26.05000,
            "desc": "Campus modern și programe de specializare în sănătatea animalelor de companie."
        },
        {
            "name": "Universitatea de Științe Agricole și Medicină Veterinară a Banatului Timișoara",
            "rank": "Top 3 Medicină Veterinară în România",
            "url": "https://www.usab-tm.ro",
            "img": "https://www.revistafermierului.ro/media/k2/items/cache/6c1295254c1fd77b0bf5c280d7c50593_XL.jpg",
            "lat": 45.73762,
            "lon": 21.22724,
            "desc": "Programe de medicină veterinară cu accent pe boli și chirurgie animală."
        }
    ],
    "Arhitect": [
        {
            "name": "Universitatea de Arhitectură și Urbanism Ion Mincu București",
            "rank": "Top 1 Arhitectură în România",
            "url": "https://uauim.ro",
            "img": "https://upload.wikimedia.org/wikipedia/commons/2/22/Fac_ahitectura_Ion_Mincu.jpg",
            "lat": 44.43890,
            "lon": 26.09610,
            "desc": "Program de elită în design arhitectural și urbanism."
        },
        {
            "name": "Universitatea Politehnica Timișoara Facultatea de Arhitectură și Urbanism",
            "rank": "Top 2 Arhitectură în România",
            "url": "https://upt.ro",
            "img": "https://upload.wikimedia.org/wikipedia/commons/5/5f/Facultatea_de_Constructi-Arhitectura_Timisoara_2.jpg",
            "lat": 45.75396,
            "lon": 21.22561,
            "desc": "Excelență în proiectare urbană și tehnici moderne de construcție."
        },
        {
            "name": "Universitatea Tehnică din Cluj-Napoca Facultatea de Arhitectură și Urbanism Joseph Köteles",
            "rank": "Top 3 Arhitectură în România",
            "url": "https://utcluj.ro",
            "img": "https://clujtravel.com/wp-content/uploads/2010/09/utcn-cluj.png",
            "lat": 46.76920,
            "lon": 23.58550,
            "desc": "Program cu focus pe dezvoltare durabilă și restaurare arhitecturală."
        }
    ],
    "Farmacist": [
        {
            "name": "Universitatea de Medicină și Farmacie Carol Davila București",
            "rank": "Top 1 Farmacie în România",
            "url": "https://umfcd.ro",
            "img": "https://upload.wikimedia.org/wikipedia/commons/c/c1/Fosta_Facultate_de_Medicina_azi_Universitatea_de_Medicina_si_Farmacie%2C_Bd._Eroii_Sanitari_nr._8%2C_sect._5%2C_Bucuresti.JPG",
            "lat": 44.43528,
            "lon": 26.07000,
            "desc": "Tradiție în formare farmaceutică, cercetare în biofarmacie și farmacologie."
        },
        {
            "name": "Universitatea de Medicină și Farmacie Grigore T. Popa Iași",
            "rank": "Top 2 Farmacie în România",
            "url": "https://www.umfiasi.ro",
            "img": "https://culturainiasi.ro/wp-content/uploads/2017/06/Universitatea-de-Medicin%C4%83-%C8%99i-Farmacie-Grigore-T.-Popa-Ia%C8%99i.jpg",
            "lat": 47.16015,
            "lon": 27.59581,
            "desc": "Programe de formare farmacologică și cercetare clinico-farmaceutică."
        },
        {
            "name": "Universitatea de Medicină și Farmacie Iuliu Hațieganu Cluj-Napoca",
            "rank": "Top 3 Farmacie în România",
            "url": "https://www.umfcluj.ro",
            "img": "https://cdn.umfcluj.ro/uploads/2021/10/umfih-07.jpg",
            "lat": 46.76206,
            "lon": 23.58360,
            "desc": "Cercetare avansată în biochimie și farmacologie experimentală."
        }
    ],
    "Contabil": [
        {
            "name": "Academia de Studii Economice București Facultatea de Contabilitate și Informatică de Gestiune",
            "rank": "Top 1 Contabilitate în România",
            "url": "https://www.ase.ro",
            "img": "https://www.economistul.ro/wp-content/uploads/2024/10/ASE_Piata-Romana-resize.jpg",
            "lat": 44.44750,
            "lon": 26.09670,
            "desc": "Programe acreditate CECCAR, pregătire în audit și fiscalitate."
        },
        {
            "name": "Universitatea Alexandru Ioan Cuza Iași Economie și Business (Contabilitate)",
            "rank": "Top 2 Contabilitate în România",
            "url": "https://www.feaa.uaic.ro",
            "img": "https://keystoneacademic-res.cloudinary.com/image/upload/c_fill,w_3840,h_1645,g_auto/dpr_auto/f_auto/q_auto/v1/element/12/125533_coversize.jpg",
            "lat": 47.16222,
            "lon": 27.58889,
            "desc": "Specializări în contabilitate financiară și management financiar."
        },
        {
            "name": "Universitatea de Vest Timișoara Facultatea de Socio-Umane (Contabilitate)",
            "rank": "Top 3 Contabilitate în România",
            "url": "https://www.uvt.ro",
            "img": "https://uvt.ro/wp-content/uploads/2020/10/UVT-2-2.jpg",
            "lat": 45.74712,
            "lon": 21.23151,
            "desc": "Curriculum axat pe audit, fiscalitate și ERP în contabilitate."
        }
    ],
    "Scriitor": [
        {
            "name": "Universitatea din București Facultatea de Litere",
            "rank": "Top 1 Literatură Română în România",
            "url": "https://litere.unibuc.ro",
            "img": "https://cdn.edupedu.ro/wp-content/uploads/2020/06/Unibuc.jpg",
            "lat": 44.43556,
            "lon": 26.10112,
            "desc": "Profiluri în filologie, scriere creativă și literatură comparată."
        },
        {
            "name": "Universitatea Babeș-Bolyai Cluj-Napoca Facultatea de Litere",
            "rank": "Top 2 Literatură Română în România",
            "url": "https://litere.ubbcluj.ro",
            "img": "https://visitcluj.ro/wp-content/uploads/2021/05/Universitatea-Babes-Bolyai-UBB-PMC16609_.jpg",
            "lat": 46.76767,
            "lon": 23.59137,
            "desc": "Domenii de studiu: literatură, comunicare, jurnalism literar."
        },
        {
            "name": "Universitatea Alexandru Ioan Cuza Iași Facultatea de Litere",
            "rank": "Top 3 Literatură Română în România",
            "url": "https://www.uaic.ro",
            "img": "https://culturainiasi.ro/wp-content/uploads/2017/06/Facultatea-de-Litere.jpg",
            "lat": 47.16222,
            "lon": 27.58889,
            "desc": "Programe avansate în literatură și scriere creativă."
        }
    ],
    "Designer": [
        {
            "name": "Universitatea Națională de Arte București",
            "rank": "Top 1 Design Grafic în România",
            "url": "https://unarte.org",
            "img": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dc/UNARTE_Bucaresti_14.jpg/960px-UNARTE_Bucaresti_14.jpg",
            "lat": 44.44720,
            "lon": 26.09830,
            "desc": "Programe de design grafic, design de produs și arte vizuale."
        },
        {
            "name": "Universitatea de Artă și Design Cluj-Napoca",
            "rank": "Top 2 Design Grafic în România",
            "url": "https://uad.ro",
            "img": "https://www.uad.ro/Public/Images/01%20DESPRE%20NOI/01%20Despre%20noi/UAD_fatada.jpg",
            "lat": 46.76960,
            "lon": 23.58300,
            "desc": "Excelență în design vestimentar, design de produs și media digitală."
        },
        {
            "name": "Universitatea de Vest Timișoara Facultatea de Arte și Design",
            "rank": "Top 3 Design Grafic în România",
            "url": "https://www.uvt.ro",
            "img": "https://admitere.uvt.ro/wp-content/uploads/listing-uploads/cover/2022/05/08b.jpg",
            "lat": 45.74712,
            "lon": 21.23151,
            "desc": "Programe interdisciplinare de multimedia, design grafic și arte digitale."
        }
    ],
    "Analist de date": [
        {
            "name": "Universitatea Politehnica din București Facultatea de Automatică și Calculatoare",
            "rank": "Top 1 Data Science în România",
            "url": "https://www.acs.pub.ro",
            "img": "https://upb.ro/wp-content/uploads/2018/04/precis-upb.jpg",
            "lat": 44.43833,
            "lon": 26.05139,
            "desc": "Specializări în inteligență artificială, big data și machine learning."
        },
        {
            "name": "Universitatea Babeș-Bolyai Cluj-Napoca Facultatea de Matematică și Informatică",
            "rank": "Top 2 Data Science în România",
            "url": "https://math.ubbcluj.ro",
            "img": "https://ssmr.ro/files/newsletter/news7/UBB1.png",
            "lat": 46.76767,
            "lon": 23.59137,
            "desc": "Cursuri avansate de analiză de date, statistică și data mining."
        },
        {
            "name": "Universitatea Tehnică din Cluj-Napoca Facultatea ETTI",
            "rank": "Top 3 Data Science în România",
            "url": "https://etc.utcluj.ro",
            "img": "https://www.utcluj.ro/media/faculties/7/inginerie-electrica.jpg.1280x720_q85_crop-smart.jpg",
            "lat": 46.76920,
            "lon": 23.58550,
            "desc": "Programe de calcul paralel, big data și machine learning aplicat."
        }
    ]
}

career_images = {
    # "Programator": "https://upload.wikimedia.org/wikipedia/commons/d/da/Software_developer_at_work_02.jpg",
}

# Durata studiilor necesare (ani, aproximativ) pentru unele cariere
study_years = {
    "Medic": 10,
    "Cercetător": 8,
    "Veterinar": 6,
    "Arhitect": 6,
    "Farmacist": 5,
    "Jurist": 5
}
# Pentru celelalte cariere care nu apar aici, vom considera implicit 4 ani (o licență)

# Formular de introducere a datelor utilizatorului
with st.form("input_form"):
    favorite_subjects = st.multiselect("Materii favorite (de preferat cel puțin două):", options=subjects_list)
    work_mode = st.radio("Preferi să lucrezi:", ["Individual", "În echipă", "Ambele"], index=2)
    creativity_level = st.slider("Creativitate (0-10):", 0, 10, 5)
    people_level = st.slider("Dorința de a ajuta oamenii (0-10):", 0, 10, 5)
    leadership_level = st.slider("Spirit de lider / inițiativă (0-10):", 0, 10, 5)
    study_choice = st.radio("Cât de mult ești dispus să studiezi pentru cariera dorită?",
                             ["3-4 ani (doar licență)", "5-6 ani (master)", "7+ ani (doctorat/rezidențiat)"], index=1)
    preferred_career = st.selectbox("Domeniu preferat (opțional):", ["(Niciunul)"] + careers_list, index=0)
    submit = st.form_submit_button("Vezi recomandări AI")

# La apăsarea butonului, se procesează intrările și se generează recomandările
if submit:
    suggestions = []
    # Adaugă opțiunea preferată dacă a fost selectată
    if preferred_career and preferred_career != "(Niciunul)":
        if preferred_career in career_data:
            suggestions.append(preferred_career)
    # Calculează scorul de potrivire pentru fiecare carieră
    scores = []
    # Normalizează modul de lucru al utilizatorului pentru comparare
    user_mode_norm = "Team" if work_mode == "În echipă" else ("Individual" if work_mode == "Individual" else "Both")
    # Categorii pentru creativitate și dorința de a ajuta (low/med/high)
    if creativity_level >= 7:
        user_creativity_cat = "high"
    elif creativity_level >= 4:
        user_creativity_cat = "med"
    else:
        user_creativity_cat = "low"
    if people_level >= 7:
        user_people_cat = "high"
    elif people_level >= 4:
        user_people_cat = "med"
    else:
        user_people_cat = "low"
    # Interpretează preferința pentru durata studiilor
    if "7+" in study_choice:
        max_study = 999  # practic fără limită
    elif "5-6" in study_choice:
        max_study = 6
    else:
        max_study = 4
    # Evaluează fiecare carieră potențială
    for career_name, info in career_data.items():
        if career_name in suggestions:  # sare peste cariera preferată deja adăugată
            continue
        score = 0
        # Potrivirea materiilor
        if info["subjects"]:
            if set(favorite_subjects) & set(info["subjects"]):
                # adaugă puncte pentru fiecare materie care se potrivește
                score += 3 * len(set(favorite_subjects) & set(info["subjects"]))
            else:
                # dacă nu se potrivește nicio materie esențială (dacă există), penalizează puțin
                score -= 1
        # Potrivirea modului de lucru
        career_mode_norm = "Team" if info["mode"] in ["Team", "În echipă"] else ("Individual" if info["mode"] == "Individual" else "Both")
        if career_mode_norm == "Both" or user_mode_norm == "Both":
            score += 1  # flexibilitate
        else:
            if user_mode_norm == career_mode_norm:
                score += 2
            else:
                # penalizare dacă unul e strict individual și celălalt strict în echipă
                if (user_mode_norm == "Individual" and career_mode_norm == "Team") or (user_mode_norm == "Team" and career_mode_norm == "Individual"):
                    score -= 2
        # Potrivirea creativității
        demand_creat = info["creativity"]
        if demand_creat == "high":
            if user_creativity_cat == "high":
                score += 2
            elif user_creativity_cat == "med":
                score += 0
            else:
                score -= 3
        elif demand_creat == "med":
            if user_creativity_cat == "high":
                score += 1
            elif user_creativity_cat == "med":
                score += 2
            else:
                score -= 2
        elif demand_creat == "low":
            if user_creativity_cat == "high":
                score -= 1
            elif user_creativity_cat == "med":
                score += 0
            else:
                score += 2
        # Potrivirea dorinței de a ajuta (lucru cu oamenii)
        demand_people = info["people"]
        if demand_people == "high":
            if user_people_cat == "high":
                score += 2
            elif user_people_cat == "med":
                score += 0
            else:
                score -= 3
        elif demand_people == "med":
            if user_people_cat == "high":
                score += 1
            elif user_people_cat == "med":
                score += 2
            else:
                score -= 2
        elif demand_people == "low":
            if user_people_cat == "high":
                score -= 1
            elif user_people_cat == "med":
                score += 0
            else:
                score += 2
        # Potrivirea spiritului de lider
        if leadership_level >= 7:
            if career_name in ["Antreprenor", "Politician"]:
                score += 2
            if career_name in ["Jurist", "Profesor"]:
                score += 1
        elif leadership_level <= 3:
            if career_name in ["Antreprenor", "Politician", "Jurist"]:
                score -= 2
        # Potrivirea cu durata studiilor dorită
        required_years = study_years.get(career_name, 4)
        if max_study < required_years:
            score -= 2  # cariera necesită studii mai lungi decât e dispus utilizatorul
        elif max_study >= 7 and required_years >= 7:
            score += 1  # utilizatorul e dispus la studii lungi și cariera cere studii lungi
        scores.append((score, career_name))
    # Sortează carierele descrescător după scor
    scores.sort(reverse=True, key=lambda x: x[0])
    # Selectează primele 25 opțiuni (cele mai potrivite)
    for sc, career_name in scores[:5]:
        suggestions.append(career_name)
        if len(suggestions) >= 5:
            break
    # Elimină dublurile (dacă cariera preferată apărea și în top scor)
    suggestions = list(dict.fromkeys(suggestions))
    suggestions = suggestions[:5]

    # Afișează recomandările dacă există
    if suggestions:
        st.markdown("## 🔍 Mentorul AI ți-a recomandat următoarele cariere (apasă pe fiecare):", unsafe_allow_html=True)
        career_icons = {
            "Programator": "🚀", "Medic": "🩺", "Inginer": "⚙️", "Profesor": "📚", "Cercetător": "🔬",
            "Artist": "🎨", "Muzician": "🎵", "Jurist": "⚖️", "Jurnalist": "📰", "Economist": "💼",
            "Antreprenor": "💡", "Psiholog": "🧠", "Veterinar": "🐾", "Arhitect": "📐", "Farmacist": "💊",
            "Contabil": "📊", "Scriitor": "✒️", "Designer": "🎨", "Analist de date": "📈", "Politician": "🏛️",
            "Polițist": "👮", "Militar": "💂"
        }

        # Dropdown cu primele 5 cariere recomandate
        top5 = suggestions[:5]

        # Afișăm expandere pentru fiecare din top5, dar în layout vertical
        for career_name in top5:
            info = career_data[career_name]
            icon = career_icons.get(career_name, "🖋️")
            exp = st.expander(f"{icon} {info['title']}", expanded=False)
            with exp:
                # Motiv de potrivire
                reason = info['reason'].capitalize()
                st.markdown(f"**Ți se potrivește dacă:** {reason}.")
                # Pași concreți
                st.markdown("**Pași concreți pentru a ajunge aici:**")
                for i, step in enumerate(info['steps'], 1):
                    st.markdown(f"{i}. {step}")
                # Facultăți top
                facultati = career_top_faculties.get(career_name, [])
                if len(facultati) > 0: st.markdown(f"**🎓 Top facultăți recomandate pentru {info['title']}:**")
                for fac in facultati:
                    ci, ct = st.columns([1, 4])
                    with ci:
                        st.image(fac['img'], width=200)
                    with ct:
                        st.markdown(f"[{fac['name']}]({fac['url']}) - Locul în clasament: {fac['rank']}")
                        st.markdown(f"{fac['desc']}")

                st.markdown("---")

        # Sfat AI variabil (stil îmbunătățit)
        advice_pool = []
        advice_pool.append("Crede în tine! Continuă să lucrezi cu încredere pe drumul ales.")
        if len(favorite_subjects) >= 2:
            sbj = ", ".join(favorite_subjects[:2])
            advice_pool.append(f"Faptul că îți plac aceste materii îți deschide perspective unice în cariera ta.")
        if people_level >= 8:
            advice_pool.append("Empatia ta este un atu valoros în orice profesie.")
        if creativity_level >= 8:
            advice_pool.append("Creativitatea ta te va ajuta să inovezi și să te remarci.")
        advice = random.choice(advice_pool)
        st.markdown(
            f"<div style='background-color:#e8f5e9;padding:16px;border-radius:10px;margin-top:12px;'>"
            f"<span style='font-size:1.1em; color:#1e3a8a;'><b>💬 Sfat AI:</b> {advice}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

        # Buton de descărcare recomandări
        download_lines = []
        for career_name in top5:
            inf = career_data[career_name]
            download_lines.append(f"{inf['title']} - {inf['reason']}")
            for j, stp in enumerate(inf['steps'], 1):
                download_lines.append(f"  {j}. {stp}")
            download_lines.append("")
        st.download_button(
            "Descarcă recomandările", data="\n".join(download_lines), file_name="recomandari.txt", mime="text/plain"
        )
    else:
        st.markdown("**Nu s-au găsit recomandări** pe baza datelor introduse. Încearcă alte combinații de opțiuni!", unsafe_allow_html=True)
