import os
import json
import argparse
import math
import base64
import html
import re
from io import BytesIO
from datetime import datetime
from PIL import Image, ExifTags, ImageOps
import folium

SITE_GROUP_RADIUS_KM = 0.5
THUMBNAIL_SIZE = (760, 630)
ROUTE_ARROW_ZOOM = 5
ROUTE_ARROW_MIN_PIXEL_DISTANCE = 28
JYOTIRLINGA_MARKER_COLOR = "#ff7a00"
TEEN_DHAM_MARKER_COLOR = "#ffd600"
DEFAULT_MARKER_COLOR = "#d71920"
SUPPRESS_RED_NEAR_SPECIAL_RADIUS_KM = 2.0
MARKER_Z_INDEX_OFFSETS = {
    "teen_dham": 3000,
    "jyotirlinga": 2000,
    None: 1000,
}
DUAL_MARKER_ROTATIONS = {
    "teen_dham": -45,
    "jyotirlinga": 45,
}

JOURNAL_SOURCE_URL = "https://iaashish.wordpress.com/2026/01/22/mom-dad-india-pilgrims-tour/"

JOURNEY_JOURNAL_ENTRIES = [
    {
        "date": "📅 २०८२ माघ १६ (2026 Jan 30, Fri)",
        "paras": [
            "श्री गणेशाय नमः ! एकादश ज्योतिर्लिङ्ग तथा तीनधाम यात्रा विवरण प्रारम्भ:",
            "करिब बिहानको ११ बजे तिलगंगा, पशुपतिबाट यात्रा प्रस्थान गरी नौबिसेमा चिया नास्ता गरी नारायणगढ नजिक हुँदै हेटौँडा अनि विरगंजबाट रक्सौलमा बोर्डर क्रस गर्ने बित्तिकै रातको करिब ११ बजे खाना खुवाइवरी हिडियो।"
        ],
        "english": [
            "With prayers to Shri Ganesh, the Ekadash Jyotirlinga and Three Dham pilgrimage journal begins. Around 11 AM, the group departed from Tilganga, Pashupati, stopped for tea and snacks at Naubise, traveled past Narayangadh and Hetauda, crossed the border at Raxaul through Birgunj, ate dinner around 11 PM, and continued onward."
        ]
    },
    {
        "date": "📅 २०८२ माघ १७ ( 2026 Jan 31, Sat)",
        "paras": [
            "बिहान करिब ८ वजे बिहार हरिहर क्षेत्र सोनपुर जहाँ गजराज लाई ग्रहले तानेको बेलामा उक्त हस्तीले विष्णु भगवानको प्रार्थना गरी विष्णु भगवान स्वयं प्रकट भई गोहीलाई बचाउनु भएको ठाउँ जुन नेपालको सप्त गण्डकी अर्थात् नारायणी नदी भारतमा गंगा नदीसँग मिलन भई संगम भएको ठाउँ रहेछ।सो नदी हिउँदमा समेत आँखा एउटा तीरबाट अर्को तीर आँखाले ठम्याउन समेत कठिन हुँदो रहेछ, उक्त स्थानमा पितृ तर्पण गरियो , पश्चात अन्तर्राष्ट्रिय पिण्ड दान केन्द्र पुनः पुनः मा गएर श्राद्ध तर्पण गरी खाना खाएर बोधगया तर्फ लागियो।",
            "[NB: हरिहर क्षेत्र – यो क्षेत्र गजेन्द्र मोक्षको कथासँग जोडिएको छ। यो सहित चार ठाउँहरू भगवान विष्णुको लीला, अवतार, र धर्म स्थापनासँग प्रत्यक्ष जोडिएका छन् – अरु क्षेत्रहरुमा बराहक्षेत्र (पृथ्वीलाई पातालबाट उद्धार गर्नुभएको), मुक्तिक्षेत्र (विष्णु शालिग्राम का रूपमा निवास गर्नुभएको), कुरुक्षेत्र (श्रीकृष्णले गीताको उपदेश दिनुभएको)]"
        ],
        "english": [
            "Around 8 AM, they reached Harihar Kshetra, Sonepur in Bihar, a place connected with the Gajendra Moksha story. There, where Nepal's Sapta Gandaki/Narayani meets the Ganga, the river was so wide in winter that the opposite bank was difficult to see. They performed pitri tarpan, then went to the International Pind Daan Center at Punpun, performed shraddha and tarpan, ate, and left for Bodh Gaya.",
            "Note: Harihar Kshetra is associated with Gajendra Moksha. Along with Barahakshetra, Muktikshetra, and Kurukshetra, it is connected with Vishnu's divine acts, incarnations, and establishment of dharma."
        ]
    },
    {
        "date": "📅 २०८२ माघ १८ ( 2026 Feb 1, Sun)",
        "paras": [
            "बिहान ५ वजे बोधगया को होटलबाट उठेर नुहाई धुवाई गरी ‘गया’को फाल्गु नदीको किनारमा श्राद्ध गएर सम्पूर्ण पितृलाई अर्थात् पिता तिन पुस्ता सहित २३ जनाको नाममा पिण्डदान र तर्पण गरियो। त्यस पश्चात् माया बौद्धमाया होटलमा हाम्रै टिमका भाइहरूले पकाएको खाना खाएर भगवान बुद्धले बुद्धत्व प्राप्त गर्नु भएको बोधी वृक्ष लगायत ६, ७ वटा बुद्धका मन्दिर अनि जगन्नाथजी र कृष्णजीको मन्दिर समेतको अवलोकन गरी अटो मार्फत पुन होटलमा प्रवेश गरी बेलुकाको करिब ४ वजे आफ्नै रिजर्भ बसमा चढी झारखण्ड तर्फ लागियो। करिब ९ वजे तीर बाटोमा पर्ने झारखण्डस्थित बरही भन्ने ठाउँमा हाम्रो टिमका किचनका भाइहरू खानाको तयारी गर्दै हुनुहुन्छ।"
        ],
        "english": [
            "At 5 AM they left the hotel in Bodh Gaya, bathed, and went to the Falgu River in Gaya to perform shraddha, pind daan, and tarpan for all ancestors, including 23 names from three paternal generations. After eating food cooked by the tour team's kitchen helpers at Maya/Baudhamaya Hotel, they visited the Bodhi tree where Buddha attained enlightenment, several Buddhist temples, and the Jagannath and Krishna temples. They returned to the hotel by auto, boarded their reserved bus around 4 PM, and left toward Jharkhand. Around 9 PM near Barhi, Jharkhand, the kitchen team was preparing dinner."
        ]
    },
    {
        "date": "📅 २०८२ माघ १९ ( 2026 Feb 2, Mon)",
        "paras": [
            "बिहान बाबाधाम मा ७ घण्टा लाइन लागेर दर्शन गरे पश्चात बेलुका वासुकी धाम दर्शन गरी भोज गरेर रातभरि गाडीमा हिडियो।"
        ],
        "english": [
            "In the morning they stood in line for seven hours for darshan at Baba Dham. In the evening they visited Vasuki Dham, ate, and traveled by bus through the night."
        ]
    },
    {
        "date": "📅 २०८२ माघ २० ( 2026 Feb 3, Tues)",
        "paras": [
            "गंगासागरमा स्नान गरी सो दिन काकद्विप मा खाना खाई होटलमा बास बसियो।"
        ],
        "english": [
            "They bathed at Gangasagar, ate at Kakdwip that day, and stayed overnight at a hotel."
        ]
    },
    {
        "date": "📅 २०८२ माघ २१ ( 2026 Feb 4, Wed)",
        "paras": [
            "बिहान करिब १० वजे खाना खाएर स्टीमर करिब आधा घण्टा चढेपछि गंगाको द्वीप करिब २५ KM को यात्रा बसमा गरी गंगासागरमा मिलेको संगम मा पुगियो। ______ कपिलमुनिको दर्शन गरियो। ______ माताको दर्शन गर्न प्रस्थान _____।"
        ],
        "english": [
            "After eating around 10 AM, they rode a steamer for about half an hour, then traveled roughly 25 km by bus across the Ganga island to the confluence at Gangasagar. They visited Kapil Muni and then set out for the next goddess temple, with some details left blank in the diary."
        ]
    },
    {
        "date": "📅 २०८२ माघ २२ ( 2026 Feb 5, Thurs)",
        "paras": [
            "बिहान करिब ६ बजे बस उडिसा, बालेश्वर सुवर्ण रेखा नदीको तटमा पश्चात सबैजनाले नुहाई धुवाई गरेका थियौ र साथमा ल्याएको सातु खाई उडिसा स्थित भुवनेश्वर महादेव को दर्शन गर्ने तर्फ लागियो।"
        ],
        "english": [
            "Around 6 AM, the bus reached Balasore, Odisha, near the Subarnarekha River. Everyone bathed, ate the sattu they had brought, and proceeded toward darshan of Bhubaneswar Mahadev in Odisha."
        ]
    },
    {
        "date": "📅 २०८२ माघ २३ ( 2026 Feb 6, Fri)",
        "paras": [
            "उडिसा राज्यमा अवस्थित जगन्नाथ पुरी (भगवान सूर्यको कोणार्क मन्दिर प्राचीन सूर्यको दर्शन गर्ने तर्फ लागियो) गरियो। पश्चात जगन्नाथ पुरीको दर्शन गर्न पुरी नगरी तर्फ लागियो । सो मन्दिरमा ७ जना पण्डा सँग सम्पर्क गरी प्रति व्यक्ति रु. ११५१/- तिरेर फटाफट दर्शन गरी घरमा लानलाई १, १ प्याकेट प्रसाद स्वरुप दिइयो। भगवानलाई वाक र पुष्पराज बाकुली मन्दिरमा चढाउन दिनु भएको ३, ४ हजार भेटी समेत नाम सहितको रसिद काटी सोही पण्डालाई दियो। पण्डाले वाशाहरु समेतलाई प्रसाद दिनुभयो। पश्चात खिचडी, मालपुवा, जोगी तरकारी र राबडीको खाना समेत खाइयो।"
        ],
        "english": [
            "In Odisha they visited the ancient Konark Sun Temple, then traveled to Puri for darshan at Jagannath Puri. They contacted seven pandas, paid Rs. 1,151 per person for quicker darshan, received one packet of prasad each to take home, offered several thousand rupees in donations with receipts, and later ate khichdi, malpua, vegetable curry, and rabdi."
        ]
    },
    {
        "date": "📅 २०८२ माघ २४ ( 2026 Feb 7, Sat)",
        "paras": [
            "बिहान करिब ७ बजे उठेर नुहाई धुवाई गरी अलिकति हाइवेमा रहेको सारै राम्रो आन्ध्र प्रदेश स्थित नारायणको मन्दिर दर्शन गरी पेम्पा नदीमा तर्पण गरियो। पश्चात खाना खुवाइवरी आन्ध्र प्रदेशकै हैदराबाद शहरमा करिब रातीको करिब ८ वजे पुगियो, खाना खाइवरी राती नै मल्लीकार्जुन ज्योतिर्लिङ्ग (१२ ज्योतिर्लिङ्ग मध्येको १) मा दर्शन गर्न लागियो।"
        ],
        "english": [
            "Around 7 AM they woke, bathed, visited a beautiful Narayan temple by the highway in Andhra Pradesh, and performed tarpan at the Pempa River. After food, they reached Hyderabad around 8 PM, ate dinner, and left that night for darshan of Mallikarjuna Jyotirlinga, one of the twelve Jyotirlingas."
        ]
    },
    {
        "date": "📅 २०८२ माघ २५ ( 2026 Feb 8, Sun)",
        "paras": [
            "बिहान करिब ९ वजे मल्लिकार्जुन दर्शन गर्ने सिलसिलामा आन्ध्र प्रदेश स्थित श्रीशैलै मा हाम्रो बस रोकियो, पश्चात ७ वटा अटोमा म, नारायण पौडेल, रमेश पौडेल, विन्दु पौडेल, राजेन्द्र दाहाल, गंगा दाहाल, लगायत सबैजना चढी प्रत्येक व्यक्ति को रु १००/- दरले ल्याउने र लैजाने समेत, रुद्रेश्वर देवी समेत ४ मन्दिर र सबैभन्दा महत्वपूर्ण मल्लिकार्जुन ज्योतिर्लिङ्ग को दर्शन गर्न रु. २००/- तिरेर २ घण्टा लाइन बसेर बडो मुस्किलले भगवानको दर्शन गरियो। यो दर्शन हाम्रो १२ ज्योतिर्लिङ्ग मध्येको पहिलो रह्यो। (नोट: मल्लिकार्जुन ज्योतिर्लिङ्गलाई श्रीशैलै मन्दिर पनि भनिन्छ)"
        ],
        "english": [
            "Around 9 AM, the bus stopped at Srisailam in Andhra Pradesh for Mallikarjuna darshan. The group rode in seven autos, paying Rs. 100 each for the round trip, visited Rudreshwar Devi and other temples, and paid Rs. 200 for darshan of the main Mallikarjuna Jyotirlinga. After two difficult hours in line, they received darshan. This became their first Jyotirlinga darshan of the journey. Mallikarjuna is also called Srisailam Temple."
        ]
    },
    {
        "date": "📅 २०८२ माघ २६ ( 2026 Feb 9, Mon)",
        "paras": [
            "बिहान ८ वजे तिरुपति वेङ्कटेश्वर बालाजी को दर्शनार्थ बिहानको स्नानादी गरी प्रतिव्यक्ति रु ६५०/- को भाडादर निर्धारण गरी मोवाइल आदि बसमै राखेर १ गाडीमा १० जना राखेर २०-२५ KM को दुरी पार गरेर तिरुमलामा भगवान दर्शन गर्न प्रस्थान गरियो। प्रवेश द्वारको मुल गेटमा झोला र शरीर चेक जाँच गरी अगाडि बढी गणेश भगवानको दर्शन गर्न गाडी रोकी दर्शन गरी यात्रा अगाडि बढ्यो। आन्ध्र प्रदेशको तिरुमलामा पर्वतमा अवस्थित स्वामी वेङ्कटेश्वर भगवानको दर्शन गरी हाम्रो गाडीको ड्राइभरले सर्व बाधा भएको लागि केही बिधी पार गरी दर्शनार्थी दिर्घामा लाइनवद्ध रहँदा तातो तातो दुध निःशुल्क पिलाउनु भयो। अगाडि ठुलो हलमा लगेर हामीलाई राखियो सो ठाउँमा पिउने पानी र निःशुल्क शौचालयको व्यवस्था थियो। हामीले टिकट लिँदा भोलि बिहानको ४:३० मा दर्शनको व्यवस्था मिलाइएको थियो तर बेलुकाको ७, ८ वजे नै तिरुपति बालाजीको दर्शन गर्न सफल भयौं। १० वजे राती तिरुपति आन्ध्र प्रदेशबाट विदा भयौं। रात भरि यात्रा।"
        ],
        "english": [
            "At 8 AM they prepared for darshan of Tirupati Venkateswara Balaji. They left phones in the bus, paid Rs. 650 per person for transport, and traveled 20-25 km to Tirumala in vehicles carrying ten people each. After security checks and Ganesh darshan, they entered the queue, where hot milk was served free. Although their ticket was for 4:30 the next morning, they were able to complete Balaji darshan by about 7-8 PM. They left Tirupati around 10 PM and traveled overnight."
        ]
    },
    {
        "date": "📅 २०८२ माघ २७ ( 2026 Feb 10, Tues)",
        "paras": [
            "बिहान ४ बजे नुवाई धुवाई गरी काञ्चीपुरमको एकाम्बरेश्वर शिव मन्दिर र अरुल्मिगु श्री वरदराज पेरुमाल विष्णु मन्दिर मा दर्शन गरी रु. १५० को टेम्पूभाडा दर कायम गरी पछि हामी बस आन्ध्र प्रदेशमै छोडेर अर्को सानो लोकल बसमा केरला स्थित पद्मनाभ विष्णु तमिलनाडु स्थित तिरुकलुकुन्द्रम् मा रहेको अरुल्मिगु श्री वेदगिरीश्वर मन्दिर भगवानको दर्शन गर्न गयौ जुन भगवान हिन्दुहरूको सबै भन्दा धनी सुनै सुनको विशाजमान हुनुहुन्छ। सोही दर्शन गरियो।"
        ],
        "english": [
            "At 4 AM they bathed and visited Ekambareswarar Shiva Temple and Arulmigu Sri Varadaraja Perumal Vishnu Temple in Kanchipuram, paying Rs. 150 for tempo transport. Leaving the bus behind in Andhra Pradesh, they took a smaller local bus toward Kerala/Tamil Nadu and visited Arulmigu Sri Vedagiriswarar Temple at Thirukalukundram, described as a wealthy golden Vishnu temple."
        ]
    },
    {
        "date": "📅 २०८२ माघ २८ ( 2026 Feb 11, Wed)",
        "paras": [
            "हाम्रो यात्रा तमिलनाडुस्थित तिरुचिरापल्ली (ट्रिची) शहर नजिक रहेको श्री रंगनाथ स्वामी मन्दिर तर्फ लागियो। करिब रातको ८ वजे हाम्रो बस त्यही छोडी नुहाउने कपडा श्राद्धका सामान रामेश्वरममा चढाउने पूजा सामान आदि समेत लिएर अर्को लोकल बसमा रु. १५०/- प्रति व्यक्ति तिरेर रामेश्वरमको पण्डा गुरुको होटलमा खाना खाई वरी बास बसियो। पण्डा गुरुको निर्देशनमा पिण्डदान पश्चात २२ कुण्डमा स्नान गर्ने निर्देशन थियो।"
        ],
        "english": [
            "The journey continued toward Sri Ranganathaswamy Temple near Tiruchirappalli/Trichy in Tamil Nadu. Around 8 PM they left the bus with bathing clothes, shraddha materials, and offerings for Rameswaram, took another local bus for Rs. 150 per person, ate at the panda guru's hotel in Rameswaram, and stayed there. The panda guru instructed them to perform pind daan and then bathe in the 22 kunds."
        ]
    },
    {
        "date": "📅 २०८२ माघ २९ ( 2026 Feb 12, Thurs)",
        "paras": [
            "रामेश्वरम को समुद्र किनारमा नुवाई धुवाई सकेर आमाबाबुको पितृका नाममा तर्पण गरियो । पश्चात पिण्डदान गरियो। पछि हाम्रै होटलका दक्षिणा रु ५००/- समेत दिइयो। पश्चात हामी सामूहिक रुपमा नै गुरु पण्डा को निर्देशन अनुसार चिसो कपडामै भगवान रामनाथ स्वामी र रामेश्वरम मन्दिरमा प्रवेश गर्‍यौ र २२ कुण्ड मा स्नान र दर्शनको निमित्त प्रति व्यक्ति रु ६५/- १ लेरी भएर रु ५००/- तिरियो। ६२५ तिरी कुण्डमा नुहाउने र दर्शन गर्ने काम भयो। पश्चात प्रतिव्यक्ति रु १०० तिरी ट्याम्पूमा समुद्र किनारमा विभिन्न देवी देवता राम, जानकी, लक्ष्मण को दर्शन गरी बेलुका ५ वजे आफ्नै बसमा चढियो र करिब ३०० KM को दुरी पार गरी India को सवै दक्षिणमा रहेको कन्याकुमारी तर्फ प्रस्थान गरियो।"
        ],
        "english": [
            "After bathing on the seashore at Rameswaram, they performed tarpan and pind daan for their parents' ancestors and gave Rs. 500 dakshina at the hotel. Following the guru panda's instructions, they entered Ramanathaswamy/Rameswaram Temple in wet clothes for the 22 kund baths and darshan, paying the required fees. Later, they paid Rs. 100 each for a tempo to visit seaside shrines of Ram, Janaki, Lakshman, and other deities. At 5 PM they boarded their own bus and traveled about 300 km toward Kanyakumari, the southern tip of India."
        ]
    },
    {
        "date": "📅 २०८२ फागुन १ ( 2026 Feb 13, Fri)",
        "paras": [
            "बिहान ४ वजे हिन्द महासागर, अरब महासागर र वंगालको खाडी समेत को पवित्र संगममा छलमा बसी बडो आनन्दका साथ नुहाइयो। पवित्र पितृका नाममा तर्पण गरियो। पश्चात सूर्योदयको आनन्द पछि करिब १ घण्टा लामबद्ध भई कन्याकुमारी माता को दर्शन भयो। पश्चात हाम्रो बस कन्याकुमारीमै राखी अर्को सानो र खट्टा बसमा केरलामा रहेको हिन्दु मन्दिर मध्येको सवभन्दा धनी मन्दिर मानिने भगवान विष्णुको पद्मनाभम् मन्दिर मा दर्शन गरियो। सो मन्दिरमा कुर्था सुरुवाल वर्जित भएकोले भाडा रु ५० मा प्राय सवै साथीले धोती किनेर नगाई दर्शन गरियो। पश्चात पुनः तामिलनाडु फर्कियो।"
        ],
        "english": [
            "At 4 AM they joyfully bathed at the sacred meeting of the Indian Ocean, Arabian Sea, and Bay of Bengal, and performed tarpan for the ancestors. After enjoying sunrise, they stood in line for about an hour for darshan of Kanyakumari Mata. Leaving the bus in Kanyakumari, they took a smaller bus to Kerala to visit Padmanabhaswamy Temple, regarded as one of the richest Hindu temples. Because kurtha-suruwal was not allowed, many bought or rented dhotis for Rs. 50 before darshan, then returned to Tamil Nadu."
        ]
    },
    {
        "date": "📅 २०८२ फागुन २ ( 2026 Feb 14, Sat)",
        "paras": [
            "तामिलनाडुको मधुराइ शहरमा रहेको पवित्र मिनाक्षी देवीको मन्दिर बसबाट उत्रिएर नुहाई धुवाई गरी पैदलै गई करिब २ घण्टा पंक्तिबद्ध भई सुन्देश्वर शिव सहितको दर्शन गरियो। मिनाक्षी मन्दिर संसारकै हिन्दु मन्दिर मध्ये ठुलो मानिँदो रहेछ। यहाँको मन्दिरहरूमा हाफ पाइन्ट लगाउन प्राय वर्जित रहेछ। त्यसैले एउटा सानो नायलुनको रुमाल (गम्छा) लाई लगाउन धोती राखेर लगियो। त्यसै मन्दिरमा त्यसरी नै धोती पहिरिई दर्शन गरियो। मन्दिरमा प्राचीन ढुङ्गाका १००० वटा खम्बा रहेछन्। देवी मिनाक्षीलाई कुनै देवीको श्राप परेर जन्मजात ३ स्तन भएको र भगवान शिवजीको कठीन तपस्या गरी स्वयं शिव सुन्देश्वरको रुपमा उपस्थित भई मिनाक्षीलाई वरण गरि तेस्रो स्तन गायब भएको किंवदन्ती रहेछ।"
        ],
        "english": [
            "In Madurai, Tamil Nadu, they got down from the bus, bathed, and walked to Meenakshi Amman Temple. After about two hours in line, they received darshan of Meenakshi and Sundareswarar Shiva. The temple was described as one of the largest Hindu temples in the world, with many ancient stone pillars. Because half pants were generally not allowed, a small nylon cloth/gamcha was carried and worn as a dhoti for darshan. The diary also records the legend of Meenakshi's third breast disappearing when Shiva appeared as Sundareswarar."
        ]
    },
    {
        "date": "📅 २०८२ फागुन ३ ( 2026 Feb 15, Sun)",
        "paras": [
            "कर्नाटक राज्यको सुग्रीव र भगवान रामको भेट भएको ठाउँ रहेछ। माता अंञ्जनीले हनुमानजी लाई जन्म दिएको पर्वत अंञ्जनी पर्वत अनादिकाल देखि रहेछ।"
        ],
        "english": [
            "In Karnataka they visited the region associated with the meeting of Sugriva and Lord Ram. They also noted Anjani Parvat, the ancient mountain where Mother Anjani is believed to have given birth to Hanuman."
        ]
    },
    {
        "date": "📅 २०८२ फागुन ४ ( 2026 Feb 16, Mon)",
        "paras": [
            "पम्पा सरोवर र अञ्जनी माताको मन्दिर को तलपट्टी गाडी विश्राम स्थलमा दिनको ११:३० को भोजन समाप्ती पश्चात हाम्रो यात्रा महाराष्ट्र तिर लागियो। रातको १०-११ बजेतिर रोडको विश्रामस्थलमा बस रोकी भोजन गरेर पूरै रात हामी हिँडिरह्यौ। र मिति ११/४ बिहान हाइवेको होटलमा बिहानको ८ वजे पुगी सौच गरी चिया पिएर हामी परैली बैजनाथ ज्योतिर्लिङ्ग धाममा स्नान गर्न गाडी रोकियो ११ वजे परैली पुगियो।"
        ],
        "english": [
            "After lunch around 11:30 below Pampa Sarovar and Anjani Mata Temple, the journey continued toward Maharashtra. The bus stopped around 10-11 PM at a roadside rest area for dinner, and they traveled all night. The next morning they reached a highway hotel around 8 AM, used the facilities, drank tea, and stopped at Parli Vaijnath Jyotirlinga Dham around 11 AM for bathing and darshan."
        ]
    },
    {
        "date": "📅 २०८२ फागुन ५ ( 2026 Feb 17, Tues)",
        "paras": [
            "परैली बैजनाथ धाम मा बिहान १० वजे गाडी रोकियो। रु. २० तिरेर नुहाई धुवाई गरी दर्शन गर्ने तर्फ लागियो। पश्चात खाना खुवाइवरी सोही ठाउँमा होटलमा बास बसियो।"
        ],
        "english": [
            "The bus stopped at Parli Vaijnath Dham around 10 AM. They paid Rs. 20 to bathe and prepare, went for darshan, ate afterward, and stayed overnight at a hotel there."
        ]
    },
    {
        "date": "📅 २०८२ फागुन ६ ( 2026 Feb 18, Wed)",
        "paras": [
            "२० औं दिन प्रातः कालिन शौच, स्नान गरी पुनः यात्रा हिँडेर भगवान घृष्णेश्वर महादेव मन्दिर पुगियो ( १२ औं ज्योतिर्लिङ्ग ) सोही राज्यमा अवस्थित भगवान घृष्णेश्वर ज्योतिर्लिङ्ग को दर्शन गरी होटलमा गएर बास बसियो।"
        ],
        "english": [
            "On the twentieth day, after morning ablutions and bathing, they continued to Grishneshwar Mahadev Temple, the twelfth Jyotirlinga. They received darshan of Grishneshwar Jyotirlinga in Maharashtra and then stayed overnight at a hotel."
        ]
    },
    {
        "date": "📅 २०८२ फागुन ७ ( 2026 Feb 19, Thurs)",
        "paras": [
            "प्रातः भगवान घृष्णेश्वर र दत्तात्रयको दर्शन गरी साझको खाना पश्चात आरम गरियो। बिहान ४:२० मा स्नानादी सकेर बिहान पुनः घृष्णेश्वर ज्योतिर्लिङ्गको दर्शन गरी अजन्ता एलोरा गुफा भ्रमण गर्न १ KM हिँडेर मात्र रु ४० तिरी अवलोकन गरियो २, ३ हजार वर्ष अगाडिका पाषाण खम्बा विग्रह हरु खुब संरक्षण गरिएका रमणीय स्थल रहेछ। हिन्दू, बुद्ध र जैन धर्म सम्बन्धी विभिन्न मूर्तिहरु कुँदिएका रहेछन्। गुफाबाट ५ बजे पुन होटलमा आई भोजन पश्चात करिब ११ बजे उक्त ठाउँबाट विदा भइयो।"
        ],
        "english": [
            "In the morning they visited Grishneshwar and Dattatreya, then rested after the evening meal. After bathing at 4:20 AM, they again visited Grishneshwar Jyotirlinga and walked about 1 km to tour the Ajanta-Ellora caves, paying Rs. 40. The diary describes the well-preserved stone pillars and sculptures, 2,000-3,000 years old, with Hindu, Buddhist, and Jain carvings. They returned to the hotel around 5 PM, ate, and left around 11 PM."
        ]
    },
    {
        "date": "📅 २०८२ फागुन ८ ( 2026 Feb 20, Fri)",
        "paras": [
            "मध्यान्ह १:३० बजे गौतमीतट भगवान त्रयम्बकेश्वर ज्योतिर्लिङ्ग क्षेत्रमा बस विश्राम गरी लामवद्ध भएर अन्दाजी १ KM पर भगवान त्रयम्बकेश्वर ज्योतिर्लिङ्ग मन्दिर मा प्रवेश गरियो। गौतमीतटमा रहेको सो मन्दिरमा हामीले नेपालबाट ल्याइएको रुद्राक्ष, पिताम्बर आदि चढायौ। करीब ४ घण्टा लामवद्ध गरी भगवानको दर्शन गरियो। शनिदेवको दर्शन गरियो।"
        ],
        "english": [
            "At 1:30 PM, the bus rested in the Gautami bank area of Trimbakeshwar Jyotirlinga. They stood in line and entered the temple about 1 km away. At the temple on the Gautami bank, they offered rudraksha and pitambar brought from Nepal. After about four hours in line, they received darshan and also visited Shani Dev."
        ]
    },
    {
        "date": "📅 २०८२ फागुन ९ ( 2026 Feb 21, Sat)",
        "paras": [
            "२२ औं दिन गुजरात एकालेश्वर भगवान को दक्षिणमा प्रभावित पवित्र नर्मदा नदीमा प्रातः ८ बजे स्नान सम्पन्न। बेलुका हाम्रो यात्रा सत्य साईबाबाकोमा भयो।"
        ],
        "english": [
            "On the twenty-second day, they bathed at 8 AM in the sacred Narmada River south of Gujarat's Ekaleshwar Bhagwan area. In the evening, the journey continued to Satya Sai Baba's place."
        ]
    },
    {
        "date": "📅 २०८२ फागुन १० ( 2026 Feb 22, Sun)",
        "paras": [
            "बेलुका गुजरात स्थित सोमनाथ ज्योतिर्लिङ्ग को दर्शन गरियो। सो ठुलो मन्दिर अरब सागरको तटमा पौडी रहेका जल देखियो अनि हामी सौराष्ट्र शहरको संगम होटलमा वास बसियो। ।"
        ],
        "english": [
            "In the evening they received darshan of Somnath Jyotirlinga in Gujarat. They saw the grand temple by the Arabian Sea and stayed overnight at Sangam Hotel in Saurashtra."
        ]
    },
    {
        "date": "📅 २०८२ फागुन ११ ( 2026 Feb 23, Mon)",
        "paras": [
            "संगम होटलमा नुहाईधुवाई गरी बिहान ४:३० मा पुनः हामी शिवको दर्शन गर्न गयौ। सोमनाथ हामीलाई बसले छोडेर करिब १५० मिटर पर गई सकेछ। होटलबाट बस रु १५००:०० लिएर फोन गरी बसलाई रोकेर गन्तव्य सम्म उसकै कारमा पुर्‍याइदियो। पश्चात हामी छाप द्वारका, भेट द्वारका नागेश्वर ज्योतिर्लिङ्ग अनि ३ धाम मध्येको १ धाम द्वारकाधिस श्री कृष्ण भगवानको दर्शन गरी सोही ठाउँमा खाना खाएर। ।"
        ],
        "english": [
            "After bathing at Sangam Hotel, they again went for Shiva darshan at 4:30 AM. The bus had moved about 150 meters away, so the hotel charged Rs. 1,500, phoned the bus, stopped it, and took them to it by car. They then visited Chhap Dwarka, Bet Dwarka, Nageshwar Jyotirlinga, and Dwarkadhish Shri Krishna, one of the three dhams, and ate there."
        ]
    },
    {
        "date": "📅 २०८२ फागुन १२ ( 2026 Feb 24, Tues)",
        "paras": [
            "करिब बिहानको १२ बजेतिर मातृगया पुगियो। नुहाई धुवाई गरी मातृ श्राद्ध गरियो पश्चात खाना खाएर बसमा हिडियो। बाटोमा खाना पकाउन बस रोकियो। हामीले श्राद्ध गरेको हुनाले रोटी र दूध मगाएर खायौ। अरु साथीले खाना खाइबरी राजस्थान तर्फ लाग्नु पर्नेमा हडताल छ भनि मध्य प्रदेश तर्फ लागियो।"
        ],
        "english": [
            "Around midnight they reached Matrugaya. After bathing, they performed maternal shraddha, ate, and continued by bus. The bus stopped on the way to cook food; because they had performed shraddha, they asked for roti and milk. Other travelers ate food. Although the plan was to go toward Rajasthan, a strike was reported, so they headed toward Madhya Pradesh instead."
        ]
    },
    {
        "date": "📅 २०८२ फागुन १३ ( 2026 Feb 25, Wed)",
        "paras": [
            "रातभरि हिँडेर बिहान मध्य प्रदेश को १ गाउँमा नुवाई धुवाई गरी चिया खाएर उज्जैन ३ घण्टाको यात्रा पछि उज्जयनी शहरमा रहेको कालभैरवको दर्शन पश्चात महाकालेश्वर ज्योतिर्लिङ्ग को खुव राम्रोसँग दर्शन गरी धन्य धन्य भइयो। राती बस करिब होटलमा बास बसियो। ॐ अङ्कार नगर उज्जैन नजिक मध्य प्रदेशमा बास बसियो। ॐ कारेश्वरबाट ८ KM वर होटलमा बास। ॐ कार होटलमा बास।"
        ],
        "english": [
            "After traveling all night, they bathed in a village in Madhya Pradesh, drank tea, and after a three-hour journey reached Ujjain. They visited Kal Bhairav, then had a very good darshan of Mahakaleshwar Jyotirlinga and felt blessed. At night they stayed near Ujjain/Omkareshwar, about 8 km before Omkareshwar, at Omkar Hotel."
        ]
    },
    {
        "date": "📅 २०८२ फागुन १४ ( 2026 Feb 26, Thurs)",
        "paras": [
            "बिहान उठेर नुहाई धुवाई गरी बसमा करिब ७८ KM हाम्रै बसमा चढी ॐ कारेश्वर महादेव दर्शन गर्ने तर्फ लागियो। सोही सिलसिलामा नर्मदा नदी को समेत मार्चन गरी जल समेत भरियो। अनि ॐ कारेश्वर ज्योतिर्लिङ्ग को सारै राम्रो सँग दर्शन गर्ने सौभाग्य प्राप्त भयो। पश्चात बाहिर आई फोटोग्राफीको काम समेत भयो अनि ममलेश्वर जुन नर्मदा नदीको तटमा हुनुहुन्छ (एउटा तटमा ॐ कारेश्वर र अर्कोमा ममलेश्वर ) को समेत धन्य धन्य भई दर्शन भयो। अनि होटलमा आई करिब ११ वजे खाना खाएर १२:३० मा ग्वालियर हिडियो। इन्दौर शहरमा जुन ठाउँमा Sheraton Hotel रहेछ। रु २०-२० को आइसक्रिम अनि १०-१० को चिया। खाना खाइयो अनि बसमा हिडियो। दिउँसो ६ वटा चिया र ६ वटा रोटी रु १२ को दरले रु ७२ मा र रु ५० को दुध खायौ। बेलुकाको खाना खाइयो। पश्चात रातभरि बसको यात्रा गरी बिहान ७ बजे U.P. को होटलमा चिया र बिस्कुटको खाजा खाइवरी ७ वटा सिता-मोला खाएर करिब ९ बजे हाम्रो बस U.P. तर्फ नै अघि बढिरह्यो। दिउँसोको करिब २ बजे ११/१५ शुक्रबार चित्रकूट नजिक सितापुर रामायण शहरको धर्मशालामा आएर हाम्रो बस रोकियो। अनि भाइहरूले खाना बनाउन लागे। मैले सोही बजारमा रु ९० को दरले ४ वटा रोटी र ड्याडल ३ रोटी, ५० को दही अनि चिया खायौ।"
        ],
        "english": [
            "After waking and bathing, they rode about 78 km in their own bus toward Omkareshwar Mahadev. They also worshipped and collected water from the Narmada River. They received very good darshan of Omkareshwar Jyotirlinga, took photos outside, and also joyfully visited Mamleshwar on the opposite bank of the Narmada. They returned to the hotel, ate around 11 AM, and left for Gwalior at 12:30. In Indore near the Sheraton Hotel, they bought ice cream and tea, ate, and continued. Later they had tea, rotis, and milk, ate dinner, traveled overnight, stopped in Uttar Pradesh for tea and biscuits, ate sita-mola, and by afternoon reached a dharmashala near Chitrakoot/Sitapur Ramayan city, where the kitchen team began preparing food."
        ]
    },
    {
        "date": "📅 २०८२ फागुन १५ ( 2026 Feb 27, Fri)",
        "paras": [
            "बिहान करिब ८ बजे U.P. को १ होटलमा नुहाइ शौच स्थान आदि गरी आफुसँग भएको सातु र चिया खाएँ। मैले बिहानको खाना खाइन किनकी आज एकादशी थियो। ड्याडीले आलु, तामाको तरकारी र भात खानुभयो। पश्चात ४ बजे तीर हामी प्रतिव्यक्ति रु ५०/- मा अटो लिएर ८ जना चित्रकुटको विभिन्न ८ मन्दिर, भरत घाट, हनुमान मन्दिर, राम शैया, फटिक शीला, सिता कुण्ड, गौरी कुण्ड आदिको दर्शन गरी करिब ७ बजे धर्मशालामा आई खाना खाइयो। पश्चात १० बजे रातीमा प्रयागराज गंगा, यमुना र सरस्वतीको संगम नजिकको ठाउँमा जानको लागि प्रस्थान गरियो। करिब ३ घण्टाको मात्र दूरी भएकोले बाटोमै बस रोकी ड्राइभर समेतले आराम गर्दै २०८२/११/१६ गते बिहान प्रयागराज पासपार्कमा आई बस रोकियो।"
        ],
        "english": [
            "Around 8 AM they bathed and used facilities at a hotel in Uttar Pradesh, then ate sattu and tea. Because it was Ekadashi, Mom did not eat the morning meal; Dad ate potato, bamboo-shoot curry, and rice. Around 4 PM, eight people took autos at Rs. 50 each to visit Chitrakoot's temples and sites, including Bharat Ghat, Hanuman Temple, Ram Shaiya, Sphatik Shila, Sita Kund, and Gauri Kund. They returned to the dharmashala around 7 PM, ate, and left around 10 PM for Prayagraj near the confluence of the Ganga, Yamuna, and Saraswati. Since it was only about three hours away, the bus stopped on the road so the driver could rest, and reached the Prayagraj bus park the next morning."
        ]
    },
    {
        "date": "📅 २०८२ फागुन १६ ( 2026 Feb 28, Sat)",
        "paras": [
            "करिब ४:३० मा बसबाट निस्किएर शौचादी कर्म सकी मुख धोइवरी नुहाउने कपडा, तर्पणका सामग्री र पूजा सामान लिएर यमुनाको तटमा अटोमा प्रतिव्यक्ति रु १० तिरी ८ जना पुगियो। अझै बिहान अँध्यारो भएकोले ३० मिनेट जति पर्खिएर प्रतिव्यक्ति रु १००/- तिरी गंगा, यमुना र सरस्वतीको त्रिवेणी मा गइयो। मध्ये नदीमा ४, ५ ओटा डुङ्गा मिलाएर करिब ७०, ८० फिटको गहिरो नदीमा बढो अनौठो तरिकाले काठको फल्याक हाली डुङ्गामा डोरी झुण्डाई प्रतिव्यक्ति थप रु ५०/- का दरले लिएर नुहाउने व्यवस्था मिलाएको रहेछ। सोही अनुरुप हामी आठै जनाले नुहायौ। त्यसभन्दा पहिला ७ वटा नरिवल थालमा राखी प्रत्येक दम्पतीलाई संकल्प गर्न लगाई नरिवलको रु १००/- र ब्राह्मण भोजनको रु १००/- गंगालाई दूध चढाउन रु २० समेत गरी राम्रो सँग स्नान गरि पुन: प्रतिव्यक्ति रु १० तिरी हाम्रो बसपार्क भएको सडकमा आइयो। पश्चात बसमा चढी मिर्जापुर जिल्ला हुँदै बाढी जिल्लाकै विन्ध्याचल शहरमा अवस्थित विन्धवासिनी देवीको करिब १ घण्टा लाइनमा लामबद्ध भई दर्शन गरियो। त्यति बेला सम्म हाम्रो खाना तयार भइसकेकोले करिब २:३० बजे खाना खाइयो। पश्चात २:३० बजेतिर हाम्रो गाडी सो ठाउँबाट वाराणसी (काशी) तर्फ हुइँकियो। रातको ९:३० बजे मात्र सिटी बाहिर Sleeper Bus जान दिने भएकोमा हाम्रो बस highway मा करिब २५-३० KM सिटी बाहिर उत्तर प्रदेश परिवहनकोमा नै बस रोकी उत्तर प्रदेशकै वाराणसी बसमा प्रतिव्यक्ति रु ९० तिरी वाराणसी तर्फ लागियो। बसपार्कबाट उत्रिएर पुन: प्रतिव्यक्ति रु २० तिरी अटो रिक्सामा Maruti Guest House तिर लागियो। रातमा हुनाले कपडा र श्राद्धको सामान बसमै छुटेकोले रातको ११ बजेतिर बसबाट सामान झिकेर ल्याई Guest House मा सुतियो।।"
        ],
        "english": [
            "Around 4:30 AM they left the bus, finished morning routines, and took bathing clothes, tarpan materials, and offerings to the Yamuna bank by auto for Rs. 10 per person. After waiting about 30 minutes in the dark, they paid Rs. 100 each to go to the Triveni Sangam. Several boats were tied together over the deep river, with wooden planks and ropes arranged for bathing for an extra Rs. 50 each. All eight bathed there. Before bathing, seven coconuts were placed in a tray and each couple made sankalpa, with offerings for coconuts, Brahmin bhojan, and milk for the Ganga. They returned to the bus road, then traveled through Mirzapur to Vindhyachal for darshan of Vindhyavasini Devi after about an hour in line. After lunch around 2:30 PM, they left for Varanasi/Kashi. Because sleeper buses were only allowed into the city after 9:30 PM, they parked 25-30 km outside and took a Uttar Pradesh transport bus for Rs. 90 each, then autos for Rs. 20 each to Maruti Guest House. Since clothes and shraddha materials had been left in the bus, they retrieved them around 11 PM and slept at the guest house."
        ]
    },
    {
        "date": "📅 २०८२ फागुन १७ ( 2026 Mar 1, Sun)",
        "paras": [
            "बिहान ४:३० मा उठी शौच र नुहाइधुवाई सकी ६ बजेतिर वाराणसीको गाईघाट मा पुग्यो। पश्चात ढुङ्गामा सबै ८४ घाटको दर्शन गरी मणिकर्णिका घाटमा गएर ६ पुस्ता श्राद्ध गरी सकि ८:००-१०:१५ मा विश्वनाथ ज्योतिर्लिङ्ग को दर्शनार्थ लाइनमा लागियो। करिब ४ घण्टा लामबद्ध पश्चात बल्ल विश्वनाथ शिव बाबाको दर्शन पाइयो। हामीले गंगाजल, दूध र पशुपतिनाथ बाटै रुद्राक्ष लगेका थियौ। त्यहाँको पुजारीले श्रद्धा पूर्वक चढाइदिनु भयो। पश्चात लकरमा राखिएको मोबाइल लगायतका सामान लिएर बनारसका बजारमा गई १ थालीको रु २०० मा खाना, रोटी खाइ ATM बाट पैसा झिकी प्रतिव्यक्ति रु ३० का दरले तिरी पुन: Maruti Guest House मा फर्कियो। त्यसपछि खाना खाइवरी बसमा बसी राम जन्मभूमि अयोध्या तर्फ लागियो।"
        ],
        "english": [
            "They woke at 4:30 AM, bathed, and reached Gaighat in Varanasi around 6 AM. From a boat they viewed all 84 ghats, then went to Manikarnika Ghat and completed six-generation shraddha. From 8:00 to 10:15 they stood in line for Vishwanath Jyotirlinga darshan, and after about four hours finally received darshan of Vishwanath Shiva. They had brought Gangajal, milk, and rudraksha from Pashupatinath, which the priest offered reverently. After retrieving phones and items from the locker, they ate in the Banaras market, withdrew money from an ATM, paid Rs. 30 each to return to Maruti Guest House, ate again, boarded the bus, and left for Ram Janmabhoomi, Ayodhya."
        ]
    },
    {
        "date": "📅 २०८२ फागुन १८ ( 2026 Mar 2, Sun)",
        "paras": [
            "बिहान ४ बजे अयोध्याको बाइपास पासपार्कमा रहेका पार्किङमा बस रोकियो। सबैजनाले शौच आदि गरी कसैले सरयू नदीमा त कसैले नजिकैको धारामा स्नान गर्‍यौ। सरयू नदीको मुहान मानसरोवर बाट नेपाल छिरे पछि हुम्ला कर्णाली हुँदै ७, ८ वटा कर्णाली, सेती विभिन्न नदी मिसियो बर्दियाको चिसापानी हुँदै भारत पसे पछि यसको नाम घाघरा भनिन्छ। अयोध्या नगरी वरिपरि मात्र यस नदीको नाम सरयू भनिन्छ। पश्चात अन्य ठाउँमा घाघराकै नामले चिनिन्छ र पछि गंगा नदीमा समाहित हुन्छ। अनि राम जन्मभूमि अयोध्यामा राम मन्दिर गई श्री राम चन्द्र भगवानको दर्शन गरी केही बाहिर समेतगरी करिब ९:३० मा हामी भैरहवा हुँदै नेपाल जाने भनि हिँड्यौ। करिब १२ बजे गोरखपुर नजिक बस्ती जिल्लाको एक नेशनल नजिक हाम्रो खाना खाने कार्यक्रम भयो। खाना खाएर करिब २:४५ मा बस हिँड्यो। करिब बेलुकाको ८ बजे सुनौली पुग्यौ। त्यहाँ Indian Custom मा चेक जाँच गरी सकेपछि नेपाल पट्टि आई करिब २ घण्टा बस रोकियो। सबैजना साथ जसो साथीहरूले आ-आफ्नो हिसाबले खाना, रोटी आदि खानु भयो। करिब १०:३० बजे बस गुडेर रातको १:३० मा देवघाट धाम मा आएर बस रोकियो। हामी ४:३० मा उठेर शौच आदि कर्म सम्पन्न गरी सप्तगण्डकी (नारायणी नदीमा) स्नान गरी सोही धाम नजिकैको यज्ञशालामा तीर्थ समापन यज्ञ आदि सम्पन्न गरी होटलमा रोटी, दूध र तरकारी समेत खाई करिब ९ बजे काठमाण्डौ तर्फ लाग्यो।"
        ],
        "english": [
            "At 4 AM the bus stopped at the bypass parking area in Ayodhya. Everyone completed morning routines; some bathed in the Saryu River and others at a nearby tap. The diary notes that the Saryu originates near Mansarovar, enters Nepal through Humla/Karnali, gathers several rivers including Karnali and Seti, passes through Chisapani in Bardiya into India where it is called Ghaghara, is known as Saryu around Ayodhya, and later joins the Ganga. They visited Ram Mandir at Ram Janmabhoomi for darshan of Shri Ramchandra Bhagwan, then left around 9:30 AM toward Nepal via Bhairahawa. Around noon near Gorakhpur/Basti district they stopped for lunch, left around 2:45 PM, reached Sunauli around 8 PM, cleared Indian customs, waited about two hours on the Nepal side, and ate according to individual preference. Around 10:30 PM the bus left and stopped at Devghat Dham at 1:30 AM. At 4:30 AM they completed morning routines, bathed in the Sapta Gandaki/Narayani River, performed the pilgrimage-completion yajna at the nearby yajna hall, ate roti, milk, and vegetables, and left for Kathmandu around 9 AM."
        ]
    }
]

JYOTIRLINGA_SITES = [
    ("Somnath", 20.8880, 70.4012),
    ("Mallikarjuna", 16.0733, 78.8684),
    ("Mallikarjuna", 16.0780, 78.8648),
    ("Mahakaleshwar", 23.1828, 75.7681),
    ("Omkareshwar", 22.2456, 76.1519),
    ("Kedarnath", 30.7352, 79.0669),
    ("Bhimashankar", 19.0714, 73.5357),
    ("Kashi Vishwanath", 25.3109, 83.0107),
    ("Kashi Vishwanath", 25.3179, 83.0220),
    ("Trimbakeshwar", 19.9321, 73.5317),
    ("Baidyanath", 18.8427, 76.5352),
    ("Baidyanath", 24.4922, 86.6990),
    ("Nageshwar", 22.3352, 69.0876),
    ("Rameswaram", 9.2881, 79.3174),
    ("Grishneshwar", 20.0248, 75.1791),
]

TEEN_DHAM_SITES = [
    ("Jagannath Puri", 19.8047, 85.8179),
    ("Dwarkadhish", 22.2376, 68.9674),
    ("Rameswaram", 9.2881, 79.3174),
]

UNVISITED_DHAM_SITES = [
    ("Badrinath", "Badrinath (बद्रीनाथ)", 30.7433, 79.4938),
]

UNVISITED_JYOTIRLINGA_SITES = [
    ("Kedarnath", "Kedarnath (केदारनाथ)", 30.7352, 79.0669),
    ("Bhimashankar", "Bhimashankar (भीमाशंकर)", 19.0714, 73.5357),
]

SPECIAL_SITE_POPUP_NAMES = {
    "Somnath": "Somnath (सोमनाथ), Somnath",
    "Mallikarjuna": "Mallikarjunga (मल्लिकार्जुन), Srisailam",
    "Mahakaleshwar": "Mahakaleshwar (महाकालेश्वर), Ujjain",
    "Omkareshwar": "Omkareshwar (ओंकारेश्वर), Omkareshwar",
    "Kedarnath": "Kedarnath (केदारनाथ), Kedarnath",
    "Bhimashankar": "Bhimashankar (भीमाशंकर), Bhimashankar",
    "Kashi Vishwanath": "Kashi Vishwanath (काशी विश्वनाथ), Varanasi",
    "Trimbakeshwar": "Trimbakeshwar (त्र्यंबकेश्वर), Trimbak",
    "Baidyanath": "Baidyanath (बैद्यनाथ), Parli Vaijnath",
    "Nageshwar": "Nageshwar (नागेश्वर), Dwarka",
    "Rameswaram": "Rameswaram (रामेश्वरम्), Rameswaram",
    "Grishneshwar": "Grishneshwar (घृष्णेश्वर), Ellora",
    "Jagannath Puri": "Jagannath Puri (जगन्नाथ पुरी), Puri",
    "Dwarkadhish": "Dwarkadhish (द्वारकाधीश), Dwarka",
}

SPECIAL_SITE_STATES = {
    "Somnath": "Gujarat",
    "Mallikarjuna": "Andhra Pradesh",
    "Mahakaleshwar": "Madhya Pradesh",
    "Omkareshwar": "Madhya Pradesh",
    "Kedarnath": "Uttarakhand",
    "Bhimashankar": "Maharashtra",
    "Kashi Vishwanath": "Uttar Pradesh",
    "Trimbakeshwar": "Maharashtra",
    "Baidyanath": "Maharashtra",
    "Nageshwar": "Gujarat",
    "Rameswaram": "Tamil Nadu",
    "Grishneshwar": "Maharashtra",
    "Jagannath Puri": "Odisha",
    "Dwarkadhish": "Gujarat",
}

PLACE_LABEL_STATES = {
    "Patna": "Bihar",
    "Punpun, Patna": "Bihar",
    "Bodh Gaya": "Bihar",
    "Hazaribagh": "Jharkhand",
    "Tarapith Temple, Tarapith": "West Bengal",
    "Gangasagar": "West Bengal",
    "Sagar Island": "West Bengal",
    "Kolkata": "West Bengal",
    "Chandaneswar Temple, Digha": "Odisha",
    "Puri": "Odisha",
    "Konark Sun Temple, Konark": "Odisha",
    "Draksharamam Temple, Draksharamam": "Andhra Pradesh",
    "Kanaka Durga Temple, Vijayawada": "Andhra Pradesh",
    "Kanchipuram": "Tamil Nadu",
    "Mahabalipuram": "Tamil Nadu",
    "Srirangam Temple, Tiruchirappalli": "Tamil Nadu",
    "Dhanushkodi, Rameswaram": "Tamil Nadu",
    "Kanyakumari": "Tamil Nadu",
    "Padmanabhaswamy Temple, Thiruvananthapuram": "Kerala",
    "Virupaksha Temple, Hampi": "Karnataka",
    "Shirdi": "Maharashtra",
    "Shani Shingnapur": "Maharashtra",
    "Nashik": "Maharashtra",
    "Bharuch": "Gujarat",
    "Chotila": "Gujarat",
    "Girnar, Junagadh": "Gujarat",
    "Porbandar": "Gujarat",
    "Dwarka": "Gujarat",
    "Sanand, Ahmedabad": "Gujarat",
    "Siddhpur": "Gujarat",
    "Ujjain": "Madhya Pradesh",
    "Omkareshwar Road": "Madhya Pradesh",
    "Khajuraho": "Madhya Pradesh",
    "Prayagraj": "Uttar Pradesh",
    "Vindhyachal": "Uttar Pradesh",
}

PLACE_LABELS = [
    ("Pashupatinath Temple, Kathmandu", 27.7108, 85.3481, 3),
    ("Patna", 25.5941, 85.1376, 35),
    ("Punpun, Patna", 25.5011, 85.1022, 5),
    ("Bodh Gaya", 24.6972, 84.9920, 8),
    ("Hazaribagh", 24.3690, 85.4832, 20),
    ("Tarapith Temple, Tarapith", 24.3945, 87.0870, 5),
    ("Gangasagar", 21.8846, 88.1655, 15),
    ("Sagar Island", 21.6350, 88.0780, 8),
    ("Kolkata", 22.4366, 88.2922, 20),
    ("Chandaneswar Temple, Digha", 21.7635, 87.1630, 8),
    ("Puri", 19.8650, 86.1125, 15),
    ("Konark Sun Temple, Konark", 19.8877, 86.0958, 8),
    ("Draksharamam Temple, Draksharamam", 17.2834, 82.4030, 8),
    ("Kanaka Durga Temple, Vijayawada", 16.3837, 80.5326, 12),
    ("Kanchipuram", 12.8467, 79.7006, 10),
    ("Kanchipuram", 12.8190, 79.7247, 10),
    ("Mahabalipuram", 12.6085, 80.0580, 10),
    ("Srirangam Temple, Tiruchirappalli", 10.8623, 78.6899, 8),
    ("Dhanushkodi, Rameswaram", 9.1506, 79.4491, 10),
    ("Kanyakumari", 8.0795, 77.5512, 10),
    ("Padmanabhaswamy Temple, Thiruvananthapuram", 8.3965, 76.9730, 10),
    ("Virupaksha Temple, Hampi", 15.3546, 76.4697, 8),
    ("Shirdi", 19.3813, 74.8579, 10),
    ("Shani Shingnapur", 19.3733, 74.7454, 8),
    ("Nashik", 20.0063, 73.7928, 12),
    ("Bharuch", 21.7192, 73.0454, 15),
    ("Chotila", 22.5499, 71.5934, 12),
    ("Girnar, Junagadh", 21.5278, 70.5260, 8),
    ("Porbandar", 21.7741, 69.4533, 12),
    ("Dwarka", 22.3695, 69.1082, 12),
    ("Sanand, Ahmedabad", 23.0564, 72.0417, 20),
    ("Siddhpur", 23.9090, 72.3646, 20),
    ("Ujjain", 23.2181, 75.7686, 8),
    ("Omkareshwar Road", 22.1883, 76.0707, 12),
    ("Khajuraho", 25.1580, 80.8760, 20),
    ("Prayagraj", 25.4252, 81.8834, 15),
    ("Vindhyachal", 25.1641, 82.5058, 12),
]


# Approximate state/UT capital coordinates
STATE_CAPITALS = {
    "Andhra Pradesh": ("Amaravati", 16.5062, 80.6480),
    "Arunachal Pradesh": ("Itanagar", 27.0844, 93.6053),
    "Assam": ("Dispur", 26.1433, 91.7898),
    "Bihar": ("Patna", 25.5941, 85.1376),
    "Chhattisgarh": ("Raipur", 21.2514, 81.6296),
    "Goa": ("Panaji", 15.4909, 73.8278),
    "Gujarat": ("Gandhinagar", 23.2156, 72.6369),
    "Haryana": ("Chandigarh", 30.7333, 76.7794),
    "Himachal Pradesh": ("Shimla", 31.1048, 77.1734),
    "Jharkhand": ("Ranchi", 23.3441, 85.3096),
    "Karnataka": ("Bengaluru", 12.9716, 77.5946),
    "Kerala": ("Thiruvananthapuram", 8.5241, 76.9366),
    "Madhya Pradesh": ("Bhopal", 23.2599, 77.4126),
    "Maharashtra": ("Mumbai", 19.0760, 72.8777),
    "Manipur": ("Imphal", 24.8170, 93.9368),
    "Meghalaya": ("Shillong", 25.5788, 91.8933),
    "Mizoram": ("Aizawl", 23.7271, 92.7176),
    "Nagaland": ("Kohima", 25.6751, 94.1086),
    "Odisha": ("Bhubaneswar", 20.2961, 85.8245),
    "Punjab": ("Chandigarh", 30.7333, 76.7794),
    "Rajasthan": ("Jaipur", 26.9124, 75.7873),
    "Sikkim": ("Gangtok", 27.3314, 88.6138),
    "Tamil Nadu": ("Chennai", 13.0827, 80.2707),
    "Telangana": ("Hyderabad", 17.3850, 78.4867),
    "Tripura": ("Agartala", 23.8315, 91.2868),
    "Uttar Pradesh": ("Lucknow", 26.8467, 80.9462),
    "Uttarakhand": ("Dehradun", 30.3165, 78.0322),
    "West Bengal": ("Kolkata", 22.5726, 88.3639),
    "Delhi": ("New Delhi", 28.6139, 77.2090),
    "Jammu and Kashmir": ("Srinagar/Jammu", 34.0837, 74.7973),
    "Ladakh": ("Leh", 34.1526, 77.5771),
    "Puducherry": ("Puducherry", 11.9416, 79.8083),
}


def dms_to_decimal(dms, ref):
    degrees = float(dms[0])
    minutes = float(dms[1])
    seconds = float(dms[2])

    decimal = degrees + minutes / 60 + seconds / 3600

    if ref in ["S", "W"]:
        decimal = -decimal

    return decimal


def get_exif_data(image_path):
    image = Image.open(image_path)
    raw_exif = image._getexif()

    if not raw_exif:
        return {}

    exif = {}
    for tag_id, value in raw_exif.items():
        tag = ExifTags.TAGS.get(tag_id, tag_id)
        exif[tag] = value

    return exif


def extract_photo_info(image_path):
    exif = get_exif_data(image_path)

    gps = exif.get("GPSInfo")
    if not gps:
        return None

    gps_data = {}
    for key, value in gps.items():
        decoded_key = ExifTags.GPSTAGS.get(key, key)
        gps_data[decoded_key] = value

    try:
        lat = dms_to_decimal(
            gps_data["GPSLatitude"],
            gps_data["GPSLatitudeRef"]
        )
        lon = dms_to_decimal(
            gps_data["GPSLongitude"],
            gps_data["GPSLongitudeRef"]
        )
    except KeyError:
        return None

    date_str = exif.get("DateTimeOriginal") or exif.get("DateTime")

    taken_time = None
    if date_str:
        try:
            taken_time = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            pass

    return {
        "file": os.path.basename(image_path),
        "path": image_path,
        "lat": lat,
        "lon": lon,
        "taken_time": taken_time,
    }


def photo_duplicate_key(photo):
    stem = os.path.splitext(photo["file"])[0].upper()
    normalized_stem = re.sub(r"^IMG_E(\d+)$", r"IMG_\1", stem)

    return (
        normalized_stem,
        photo["taken_time"],
        round(photo["lat"], 5),
        round(photo["lon"], 5),
    )


def prefer_original_photo(candidate, existing):
    candidate_stem = os.path.splitext(candidate["file"])[0].upper()
    existing_stem = os.path.splitext(existing["file"])[0].upper()
    candidate_is_edit = candidate_stem.startswith("IMG_E")
    existing_is_edit = existing_stem.startswith("IMG_E")

    if candidate_is_edit == existing_is_edit:
        return candidate["file"] < existing["file"]

    return not candidate_is_edit


def remove_duplicate_photos(photo_infos):
    unique_photos = {}

    for photo in photo_infos:
        key = photo_duplicate_key(photo)
        existing = unique_photos.get(key)

        if not existing or prefer_original_photo(photo, existing):
            unique_photos[key] = photo

    return sorted(unique_photos.values(), key=lambda x: x["taken_time"])


def collect_photos(folder):
    photo_infos = []

    START_DATE = datetime(2026, 1, 29)
    END_DATE = datetime(2026, 3, 2, 23, 59, 59)

    for root, _, files in os.walk(folder):
        for file in files:
            if file.lower().endswith((".jpg", ".jpeg")):
                path = os.path.join(root, file)

                info = extract_photo_info(path)

                if not info:
                    continue

                if not info["taken_time"]:
                    continue

                if START_DATE <= info["taken_time"] <= END_DATE:
                    photo_infos.append(info)

    photo_infos.sort(key=lambda x: x["taken_time"])

    return remove_duplicate_photos(photo_infos)


def distance_km(point_a, point_b):
    lat1, lon1 = map(math.radians, point_a)
    lat2, lon2 = map(math.radians, point_b)
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return 6371.0 * c


def group_photos_by_site(photo_infos, radius_km=SITE_GROUP_RADIUS_KM):
    groups = []

    for photo in photo_infos:
        point = [photo["lat"], photo["lon"]]

        if groups and distance_km(groups[-1]["center"], point) <= radius_km:
            group = groups[-1]
            group["photos"].append(photo)
            group["center"] = [
                sum(item["lat"] for item in group["photos"]) / len(group["photos"]),
                sum(item["lon"] for item in group["photos"]) / len(group["photos"]),
            ]
        else:
            groups.append({
                "center": point,
                "photos": [photo],
            })

    return groups


def matching_named_site(point, named_sites, radius_km=SITE_GROUP_RADIUS_KM):
    for name, lat, lon in named_sites:
        if distance_km(point, [lat, lon]) <= radius_km:
            return name

    return None


def matching_named_sites(point, named_sites, radius_km=SITE_GROUP_RADIUS_KM):
    matches = []

    for name, lat, lon in named_sites:
        if distance_km(point, [lat, lon]) <= radius_km and name not in matches:
            matches.append(name)

    return matches


def matching_place_label(point):
    closest_label = None
    closest_distance = None

    for label, lat, lon, radius_km in PLACE_LABELS:
        distance = distance_km(point, [lat, lon])
        if distance <= radius_km and (
            closest_distance is None or distance < closest_distance
        ):
            closest_label = label
            closest_distance = distance

    return closest_label


def classify_site_matches(point):
    matches = []

    for name in matching_named_sites(point, TEEN_DHAM_SITES):
        matches.append(("teen_dham", name))

    for name in matching_named_sites(point, JYOTIRLINGA_SITES):
        matches.append(("jyotirlinga", name))

    return matches


def classify_site(point):
    matches = classify_site_matches(point)
    if matches:
        return matches[0]

    return None, None


def prepare_sites_for_display(sites):
    prepared_sites = []

    for idx, site in enumerate(sites):
        site_copy = {
            "center": site["center"],
            "photos": list(site["photos"]),
            "original_index": idx,
        }
        site_matches = classify_site_matches(site["center"])
        site_category, matched_site_name = site_matches[0] if site_matches else (None, None)
        site_copy["matches"] = site_matches
        site_copy["category"] = site_category
        site_copy["matched_name"] = matched_site_name
        site_copy["place_label"] = matching_place_label(site["center"])
        site_copy["suppressed"] = False
        site_copy["route_site"] = site_copy
        prepared_sites.append(site_copy)

    special_sites = [
        site for site in prepared_sites
        if site["category"] in ("jyotirlinga", "teen_dham")
    ]

    for site in prepared_sites:
        if site["category"] or not special_sites:
            continue

        nearest_special = min(
            special_sites,
            key=lambda special: distance_km(site["center"], special["center"])
        )
        distance_to_special = distance_km(site["center"], nearest_special["center"])

        if distance_to_special <= SUPPRESS_RED_NEAR_SPECIAL_RADIUS_KM:
            site["suppressed"] = True
            site["route_site"] = nearest_special
            nearest_special["photos"].extend(site["photos"])
            nearest_special["photos"].sort(key=lambda photo: photo["taken_time"])

    display_sites = [site for site in prepared_sites if not site["suppressed"]]
    route_sites = [site["route_site"] for site in prepared_sites]

    route_points = []
    for site in route_sites:
        point = site["center"]
        if not route_points or route_points[-1] != point:
            route_points.append(point)

    return display_sites, route_points


def build_colored_camera_icon(color, icon_color="white", marker_rotation=0):
    return folium.DivIcon(
        class_name="colored-camera-marker",
        icon_size=(30, 30),
        icon_anchor=(15, 28),
        popup_anchor=(0, -28),
        html=f"""
        <div style="
            position: relative;
            width: 30px;
            height: 30px;
            transform: rotate({marker_rotation}deg);
            transform-origin: 15px 28px;
        ">
            <div style="
                background: {color};
                border: 2px solid white;
                border-radius: 50% 50% 50% 0;
                box-shadow: 0 1px 4px rgba(0, 0, 0, 0.35);
                height: 24px;
                left: 3px;
                position: absolute;
                top: 0;
                transform: rotate(-45deg);
                width: 24px;
            "></div>
            <i class="fa fa-camera" style="
                color: {icon_color};
                font-size: 13px;
                left: 8px;
                line-height: 24px;
                position: absolute;
                text-align: center;
                top: 1px;
                width: 16px;
            "></i>
        </div>
        """,
    )


def build_site_icon(site_category, marker_rotation=0):
    if site_category == "jyotirlinga":
        return build_colored_camera_icon(JYOTIRLINGA_MARKER_COLOR, marker_rotation=marker_rotation)

    if site_category == "teen_dham":
        return build_colored_camera_icon(TEEN_DHAM_MARKER_COLOR, "#5a3d00", marker_rotation)

    return build_colored_camera_icon(DEFAULT_MARKER_COLOR, marker_rotation=marker_rotation)


def marker_z_index_offset(site_category):
    return MARKER_Z_INDEX_OFFSETS.get(site_category, MARKER_Z_INDEX_OFFSETS[None])


def marker_rotation(site, site_category):
    if len(site.get("matches", [])) > 1:
        return DUAL_MARKER_ROTATIONS.get(site_category, 0)

    return 0


def site_display_label(matched_site_name=None, place_label=None):
    if matched_site_name:
        return SPECIAL_SITE_POPUP_NAMES.get(matched_site_name, matched_site_name)

    return place_label


def site_state_label(matched_site_name=None, place_label=None):
    if matched_site_name:
        return SPECIAL_SITE_STATES.get(matched_site_name)

    if place_label:
        return PLACE_LABEL_STATES.get(place_label)

    return None


def site_popup_title(site_number, matched_site_name=None, place_label=None):
    label = site_display_label(matched_site_name, place_label)
    state = site_state_label(matched_site_name, place_label)

    if label and state:
        return f"Site {site_number} - {label}, {state}"

    if label:
        return f"Site {site_number} - {label}"

    return f"Site {site_number}"


def photo_to_data_uri(image_path):
    try:
        with Image.open(image_path) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail(THUMBNAIL_SIZE)
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")

            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=94, optimize=True)
    except Exception:
        return None

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def format_time(taken_time):
    if not taken_time:
        return "Time not available"

    return taken_time.strftime("%Y-%m-%d %H:%M:%S")


def journal_entry_date(entry):
    match = re.search(r"2026 (Jan|Feb|Mar) (\d{1,2})", entry["date"])
    if not match:
        return None

    return datetime.strptime(
        f"2026 {match.group(1)} {match.group(2)}",
        "%Y %b %d"
    ).date()


def journal_entries_for_site(site):
    photo_dates = {
        photo["taken_time"].date()
        for photo in site["photos"]
        if photo.get("taken_time")
    }

    return [
        entry for entry in JOURNEY_JOURNAL_ENTRIES
        if journal_entry_date(entry) in photo_dates
    ]


def html_paragraphs(paragraphs):
    return "".join(
        f"<p>{html.escape(paragraph)}</p>"
        for paragraph in paragraphs
    )


def build_journal_entries_html(entries, language):
    if not entries:
        return '<p class="pilgrim-popup-empty">No journal entry is linked to this site date.</p>'

    body_parts = []

    for entry in entries:
        paragraphs = entry["english"] if language == "english" else entry["paras"]
        body_parts.append(f"""
        <article class="pilgrim-popup-journal-entry">
            <h4>{html.escape(entry["date"])}</h4>
            {html_paragraphs(paragraphs)}
        </article>
        """)

    return "".join(body_parts)


def build_site_popup(site, site_number, matched_site_name=None, place_label=None):
    photos = site["photos"]
    popup_id = f"site-{site_number}"
    popup_title = html.escape(site_popup_title(site_number, matched_site_name, place_label))
    photo_slides = []

    for photo_index, photo in enumerate(photos):
        image_uri = photo_to_data_uri(photo["path"])
        display_style = "block" if photo_index == 0 else "none"
        file_stem = html.escape(os.path.splitext(photo["file"])[0])
        time_text = html.escape(format_time(photo["taken_time"]))

        if image_uri:
            image_html = (
                f'<img src="{image_uri}" '
                'style="width: 380px; max-height: 315px; object-fit: contain; '
                'display: block; margin: 6px 0; border-radius: 4px;">'
            )
        else:
            image_html = (
                '<div style="width: 380px; padding: 107px 0; margin: 6px 0; '
                'text-align: center; background: #f2f2f2; color: #555; '
                'border-radius: 4px;">Photo preview unavailable</div>'
            )

        photo_slides.append(f"""
        <div class="{popup_id}-photo" style="display: {display_style};">
            {image_html}
            <div class="pilgrim-popup-photo-meta">({file_stem}, {time_text}, Lat/Lon: {photo['lat']:.6f}/{photo['lon']:.6f})</div>
        </div>
        """)

    controls = ""
    if len(photos) > 1:
        controls = f"""
        <div class="pilgrim-popup-photo-controls" style="display: flex; align-items: center; justify-content: space-between; margin-top: 8px;">
            <button onclick="showSitePhoto('{popup_id}', -1)" style="cursor: pointer;">&lt;</button>
            <span id="{popup_id}-counter">1 / {len(photos)}</span>
            <button onclick="showSitePhoto('{popup_id}', 1)" style="cursor: pointer;">&gt;</button>
        </div>
        """

    site_journal_entries = journal_entries_for_site(site)
    nepali_journal = build_journal_entries_html(site_journal_entries, "nepali")
    english_journal = build_journal_entries_html(site_journal_entries, "english")

    return f"""
    <div class="pilgrim-popup-tabs" style="width: 390px;">
        <b>{popup_title}</b><br>
        <div class="pilgrim-popup-tab-buttons" role="tablist" aria-label="Site popup tabs">
            <button class="pilgrim-popup-tab active" type="button" onclick="showSitePopupTab('{popup_id}', 'pictures', this)">Pictures</button>
            <button class="pilgrim-popup-tab" type="button" onclick="showSitePopupTab('{popup_id}', 'details', this)">यात्रा विवरण</button>
            <button class="pilgrim-popup-tab" type="button" onclick="showSitePopupTab('{popup_id}', 'journal', this)">Journal</button>
        </div>
        <div class="{popup_id}-popup-panel pilgrim-popup-panel active" data-panel="pictures">
            Photos: {len(photos)}<br>
            {"".join(photo_slides)}
            {controls}
        </div>
        <div class="{popup_id}-popup-panel pilgrim-popup-panel" data-panel="details" lang="ne">
            {nepali_journal}
        </div>
        <div class="{popup_id}-popup-panel pilgrim-popup-panel" data-panel="journal" lang="en">
            {english_journal}
        </div>
    </div>
    """



def add_unvisited_pilgrimage_dots(map_obj):
    for name, display_name, lat, lon in UNVISITED_DHAM_SITES:
        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            color=TEEN_DHAM_MARKER_COLOR,
            fill=True,
            fill_color=TEEN_DHAM_MARKER_COLOR,
            fill_opacity=0.95,
            weight=2,
            popup=display_name,
            tooltip=name,
        ).add_to(map_obj)

    for name, display_name, lat, lon in UNVISITED_JYOTIRLINGA_SITES:
        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            color=JYOTIRLINGA_MARKER_COLOR,
            fill=True,
            fill_color=JYOTIRLINGA_MARKER_COLOR,
            fill_opacity=0.95,
            weight=2,
            popup=display_name,
            tooltip=name,
        ).add_to(map_obj)


def calculate_bearing(start, end):
    start_lat, start_lon = map(math.radians, start)
    end_lat, end_lon = map(math.radians, end)
    delta_lon = end_lon - start_lon

    x = math.sin(delta_lon) * math.cos(end_lat)
    y = (
        math.cos(start_lat) * math.sin(end_lat)
        - math.sin(start_lat) * math.cos(end_lat) * math.cos(delta_lon)
    )

    return (math.degrees(math.atan2(x, y)) + 360) % 360


def interpolate_point(start, end, fraction=0.8):
    return [
        start[0] + (end[0] - start[0]) * fraction,
        start[1] + (end[1] - start[1]) * fraction,
    ]


def lat_lon_to_pixel(point, zoom=ROUTE_ARROW_ZOOM):
    lat, lon = point
    sin_lat = math.sin(math.radians(lat))
    sin_lat = min(max(sin_lat, -0.9999), 0.9999)
    scale = 256 * (2 ** zoom)

    x = (lon + 180) / 360 * scale
    y = (
        0.5
        - math.log((1 + sin_lat) / (1 - sin_lat)) / (4 * math.pi)
    ) * scale

    return x, y


def points_overlap(point_a, point_b, min_pixel_distance=ROUTE_ARROW_MIN_PIXEL_DISTANCE):
    x1, y1 = lat_lon_to_pixel(point_a)
    x2, y2 = lat_lon_to_pixel(point_b)

    return math.hypot(x2 - x1, y2 - y1) < min_pixel_distance


def add_direction_arrow(map_obj, start, end, fraction):
    if start == end:
        return

    arrow_location = interpolate_point(start, end, fraction)
    rotation = calculate_bearing(start, end) - 90

    folium.Marker(
        location=arrow_location,
        icon=folium.DivIcon(
            class_name="route-arrow-icon",
            icon_size=(24, 24),
            icon_anchor=(12, 12),
            html=f"""
            <div style="
                color: red;
                font-size: 22px;
                font-weight: 700;
                line-height: 24px;
                text-align: center;
                transform: rotate({rotation:.1f}deg);
                transform-origin: center center;
            ">➜</div>
            """,
        ),
    ).add_to(map_obj)


def add_route_arrows(map_obj, route_points):
    arrow_locations = []

    for start, end in zip(route_points, route_points[1:]):
        for fraction in (0.2, 0.5):
            arrow_location = interpolate_point(start, end, fraction)
            if any(points_overlap(arrow_location, existing) for existing in arrow_locations):
                continue

            add_direction_arrow(map_obj, start, end, fraction)
            arrow_locations.append(arrow_location)


def add_fixed_legend(map_obj):
    legend_html = f"""
    <div>
        <div style="display: flex; align-items: center; gap: 7px; margin: 2px 0; white-space: nowrap;">
            <span style="align-items: center; background: {DEFAULT_MARKER_COLOR}; border: 1px solid white; border-radius: 50% 50% 50% 0; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.25); color: white; display: flex; height: 14px; justify-content: center; line-height: 14px; transform: rotate(-45deg); width: 14px;">
            </span>
            <span>Sites</span>
        </div>
        <div style="display: flex; align-items: center; gap: 7px; margin: 2px 0; white-space: nowrap;">
            <span style="align-items: center; background: {TEEN_DHAM_MARKER_COLOR}; border: 1px solid white; border-radius: 50% 50% 50% 0; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.25); color: #5a3d00; display: flex; height: 14px; justify-content: center; line-height: 14px; transform: rotate(-45deg); width: 14px;">
            </span>
            <span>Dham</span>
        </div>
        <div style="display: flex; align-items: center; gap: 7px; margin: 2px 0; white-space: nowrap;">
            <span style="align-items: center; background: {JYOTIRLINGA_MARKER_COLOR}; border: 1px solid white; border-radius: 50% 50% 50% 0; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.25); color: white; display: flex; height: 14px; justify-content: center; line-height: 14px; transform: rotate(-45deg); width: 14px;">
            </span>
            <span>Jyotirlinga</span>
        </div>
    </div>
    """
    map_obj.get_root().script.add_child(folium.Element(f"""
    (function() {{
        function addPilgrimLegend() {{
            var existing = document.getElementById("pilgrim-map-legend-fixed");
            if (existing) {{
                existing.remove();
            }}

            var legend = document.createElement("div");
            legend.id = "pilgrim-map-legend-fixed";
            legend.innerHTML = {json.dumps(legend_html)};
            legend.style.position = "fixed";
            legend.style.top = "12px";
            legend.style.right = "70px";
            legend.style.zIndex = "650";
            legend.style.background = "rgba(255, 255, 255, 0.98)";
            legend.style.border = "2px solid rgba(0, 0, 0, 0.45)";
            legend.style.borderRadius = "4px";
            legend.style.boxShadow = "0 2px 8px rgba(0, 0, 0, 0.35)";
            legend.style.color = "#111";
            legend.style.fontFamily = "Arial, sans-serif";
            legend.style.fontSize = "13px";
            legend.style.lineHeight = "18px";
            legend.style.padding = "8px 10px";
            legend.style.pointerEvents = "auto";
            document.body.appendChild(legend);
        }}

        if (document.readyState === "loading") {{
            document.addEventListener("DOMContentLoaded", addPilgrimLegend);
        }} else {{
            addPilgrimLegend();
        }}
        window.setTimeout(addPilgrimLegend, 500);
    }})();
    """))


def add_fixed_title(map_obj):
    title_html = """
    <div style="font-weight: 700;">Narayan Punyawati India Pilgrim Tour 2026</div>
    <div style="font-weight: 600;">नारायण पुण्यवती धार्मिक भ्रमण २०८२</div>
    """
    map_obj.get_root().header.add_child(folium.Element("""
    <style>
        #pilgrim-map-legend-fixed {
            font-size: 9px !important;
            line-height: 12px !important;
            min-width: 58px !important;
            padding: 4px 5px !important;
            border-width: 1px !important;
        }

        #pilgrim-map-title-fixed {
            font-size: 12px !important;
            line-height: 18px !important;
            padding: 0 !important;
        }

        @media (max-width: 700px) {
            #pilgrim-map-title-fixed {
                top: 7px !important;
                left: 8px !important;
                right: 8px !important;
                transform: none !important;
                font-size: 10px !important;
                line-height: 15px !important;
                padding: 0 !important;
                white-space: normal !important;
            }

            #pilgrim-map-legend-fixed {
                top: 52px !important;
                right: 8px !important;
                font-size: 8px !important;
                line-height: 11px !important;
                min-width: 52px !important;
                padding: 3px 4px !important;
            }
        }
    </style>
    """))
    map_obj.get_root().script.add_child(folium.Element(f"""
    (function() {{
        function addPilgrimMapTitle() {{
            var existing = document.getElementById("pilgrim-map-title-fixed");
            if (existing) {{
                existing.remove();
            }}

            var title = document.createElement("div");
            title.id = "pilgrim-map-title-fixed";
            title.innerHTML = {json.dumps(title_html)};
            title.style.position = "fixed";
            title.style.top = "12px";
            title.style.left = "50%";
            title.style.transform = "translateX(-50%)";
            title.style.zIndex = "640";
            title.style.background = "transparent";
            title.style.border = "none";
            title.style.borderRadius = "0";
            title.style.boxShadow = "none";
            title.style.color = "#111";
            title.style.fontFamily = "Arial, sans-serif";
            title.style.fontSize = "15px";
            title.style.lineHeight = "24px";
            title.style.padding = "0";
            title.style.textAlign = "center";
            title.style.textShadow = "0 0 3px white, 0 0 5px white";
            title.style.whiteSpace = "nowrap";
            title.style.pointerEvents = "none";
            document.body.appendChild(title);
        }}

        if (document.readyState === "loading") {{
            document.addEventListener("DOMContentLoaded", addPilgrimMapTitle);
        }} else {{
            addPilgrimMapTitle();
        }}
        window.setTimeout(addPilgrimMapTitle, 500);
    }})();
    """))


def create_map(photo_infos, output_html, states_geojson=None):
    india_map = folium.Map(
        location=[22.5, 79.0],
        zoom_start=5,
        tiles="CartoDB positron",
        control_scale=True
    )
    for child in india_map._children.values():
        if isinstance(child, folium.raster_layers.TileLayer):
            child.show = True
            child.overlay = True
            child.control = False

    add_fixed_legend(india_map)
    add_fixed_title(india_map)
    india_map.get_root().html.add_child(folium.Element("""
    <style>
        .leaflet-popup-pane {
            z-index: 5000 !important;
        }

        .leaflet-popup {
            z-index: 5001 !important;
        }

        .leaflet-popup-content-wrapper,
        .leaflet-popup-tip {
            background: #ffffff !important;
            opacity: 1 !important;
        }

        .leaflet-popup-content {
            background: #ffffff !important;
            opacity: 1 !important;
        }

        .pilgrim-popup-tabs {
            background: #ffffff;
            opacity: 1;
        }

        body.pilgrim-popup-open #pilgrim-map-title-fixed,
        body.pilgrim-popup-open #pilgrim-map-legend-fixed {
            display: none !important;
        }

        .pilgrim-popup-tab-buttons {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            margin: 8px 0;
            border: 1px solid #d8d1c5;
            border-radius: 4px;
            overflow: hidden;
        }

        .pilgrim-popup-tab {
            background: #f5f2ec;
            border: 0;
            border-right: 1px solid #d8d1c5;
            cursor: pointer;
            font: 700 12px/1.2 Arial, sans-serif;
            min-height: 34px;
            padding: 6px 4px;
        }

        .pilgrim-popup-tab:last-child {
            border-right: 0;
        }

        .pilgrim-popup-tab.active {
            background: #ffffff;
            box-shadow: inset 0 -3px 0 #d71920;
        }

        .pilgrim-popup-panel {
            display: none;
            height: 405px;
            overflow: hidden;
        }

        .pilgrim-popup-panel.active {
            display: block;
        }

        .pilgrim-popup-panel[data-panel="pictures"].active {
            display: flex;
            flex-direction: column;
        }

        .pilgrim-popup-panel[data-panel="details"],
        .pilgrim-popup-panel[data-panel="journal"] {
            overflow-y: auto;
            padding-right: 4px;
        }

        .pilgrim-popup-photo-controls {
            margin-top: auto !important;
            min-height: 30px;
        }

        .pilgrim-popup-photo-meta {
            font-size: 11px;
            line-height: 15px;
            margin-top: 4px;
            overflow-wrap: anywhere;
        }

        .pilgrim-popup-journal-entry {
            border-bottom: 1px solid #e6e0d8;
            margin-bottom: 10px;
            padding-bottom: 8px;
        }

        .pilgrim-popup-journal-entry:last-child {
            border-bottom: 0;
            margin-bottom: 0;
        }

        .pilgrim-popup-journal-entry h4 {
            font-size: 13px;
            line-height: 1.25;
            margin: 0 0 6px;
        }

        .pilgrim-popup-journal-entry p,
        .pilgrim-popup-empty {
            font-size: 12px;
            line-height: 1.35;
            margin: 0 0 8px;
        }
    </style>
    <script>
        window.sitePhotoIndexes = window.sitePhotoIndexes || {};

        function syncPilgrimPopupOverlayState() {
            var hasOpenPopup = !!document.querySelector(".leaflet-popup-pane .leaflet-popup");
            document.body.classList.toggle("pilgrim-popup-open", hasOpenPopup);
        }

        function watchPilgrimPopups() {
            var popupPane = document.querySelector(".leaflet-popup-pane");
            if (!popupPane || !window.MutationObserver) {
                window.setTimeout(watchPilgrimPopups, 100);
                return;
            }

            var observer = new MutationObserver(syncPilgrimPopupOverlayState);
            observer.observe(popupPane, { childList: true, subtree: true });
            syncPilgrimPopupOverlayState();
        }

        if (document.readyState === "loading") {
            document.addEventListener("DOMContentLoaded", watchPilgrimPopups);
        } else {
            watchPilgrimPopups();
        }


        function showSitePhoto(siteId, direction) {
            var slides = document.getElementsByClassName(siteId + "-photo");
            if (!slides.length) {
                return;
            }

            var current = window.sitePhotoIndexes[siteId] || 0;
            slides[current].style.display = "none";
            current = (current + direction + slides.length) % slides.length;
            slides[current].style.display = "block";
            window.sitePhotoIndexes[siteId] = current;

            var counter = document.getElementById(siteId + "-counter");
            if (counter) {
                counter.textContent = (current + 1) + " / " + slides.length;
            }
        }

        function showSitePopupTab(siteId, panelName, tabButton) {
            var root = tabButton.closest(".pilgrim-popup-tabs");
            if (!root) {
                return;
            }

            root.querySelectorAll(".pilgrim-popup-tab").forEach(function(tab) {
                tab.classList.toggle("active", tab === tabButton);
            });
            root.querySelectorAll("." + siteId + "-popup-panel").forEach(function(panel) {
                panel.classList.toggle(
                    "active",
                    panel.getAttribute("data-panel") === panelName
                );
            });
        }
    </script>
    """))

    # Optional India state boundary GeoJSON
    if states_geojson:
        with open(states_geojson, "r", encoding="utf-8") as f:
            geojson_data = json.load(f)

        folium.GeoJson(
            geojson_data,
            name="India State Boundaries Halo",
            control=False,
            style_function=lambda feature: {
                "fill": False,
                "color": "white",
                "weight": 8,
                "opacity": 0.9,
            }
        ).add_to(india_map)

        folium.GeoJson(
            geojson_data,
            name="India State Boundaries",
            style_function=lambda feature: {
                "fill": False,
                "color": "#111111",
                "weight": 5,
                "opacity": 1.0,
            }
        ).add_to(india_map)

    # Add state capital markers
    for state, (capital, lat, lon) in STATE_CAPITALS.items():
        folium.CircleMarker(
            location=[lat, lon],
            radius=3,
            color="blue",
            fill=True,
            fill_opacity=0.8,
            popup=f"{capital}<br>{state}"
        ).add_to(india_map)

    add_unvisited_pilgrimage_dots(india_map)

    # Add one marker per nearby-photo site.
    sites, route_points = prepare_sites_for_display(group_photos_by_site(photo_infos))

    red_sites = [site for site in sites if not site["category"]]
    special_sites = [site for site in sites if site["category"]]

    for idx, site in enumerate(red_sites + special_sites, start=1):
        site["display_number"] = idx

    marker_entries = []

    for site in red_sites:
        marker_entries.append((site, None, None))

    for category in ("jyotirlinga", "teen_dham"):
        for site in special_sites:
            for site_category, matched_site_name in site["matches"]:
                if site_category == category:
                    marker_entries.append((site, site_category, matched_site_name))

    for site, site_category, matched_site_name in marker_entries:
        lat, lon = site["center"]
        site_number = site["display_number"]
        place_label = site["place_label"]
        label = site_display_label(matched_site_name, place_label)
        tooltip = f"Site {site_number}"
        if label:
            tooltip += f" - {label}"

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(
                build_site_popup(site, site_number, matched_site_name, place_label),
                max_width=430
            ),
            tooltip=tooltip,
            icon=build_site_icon(site_category, marker_rotation(site, site_category)),
            z_index_offset=marker_z_index_offset(site_category)
        ).add_to(india_map)

    # Draw route line
    if len(route_points) >= 2:
        route_line = folium.PolyLine(
            route_points,
            color="red",
            weight=4,
            opacity=0.8,
            tooltip="Photo route by time"
        ).add_to(india_map)

        add_route_arrows(india_map, route_points)

    folium.LayerControl().add_to(india_map)
    india_map.save(output_html)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--photo-folder", required=True)
    parser.add_argument("--output", default="india_photo_route_map.html")
    parser.add_argument("--states-geojson", default=None)

    args = parser.parse_args()

    photos = collect_photos(args.photo_folder)

    print(f"Found {len(photos)} photos with GPS data.")

    if not photos:
        print("No GPS-tagged JPG photos found.")
        return

    create_map(
        photo_infos=photos,
        output_html=args.output,
        states_geojson=args.states_geojson
    )

    print(f"Map saved to: {args.output}")


if __name__ == "__main__":
    main()
