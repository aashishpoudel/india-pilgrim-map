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
THUMBNAIL_SIZE = (360, 260)
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


def site_popup_title(site_number, matched_site_name=None, place_label=None):
    label = site_display_label(matched_site_name, place_label)
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
            image.save(buffer, format="JPEG", quality=82)
    except Exception:
        return None

    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/jpeg;base64,{encoded}"


def format_time(taken_time):
    if not taken_time:
        return "Time not available"

    return taken_time.strftime("%Y-%m-%d %H:%M:%S")


def build_site_popup(site, site_number, matched_site_name=None, place_label=None):
    photos = site["photos"]
    popup_id = f"site-{site_number}"
    popup_title = html.escape(site_popup_title(site_number, matched_site_name, place_label))
    photo_slides = []

    for photo_index, photo in enumerate(photos):
        image_uri = photo_to_data_uri(photo["path"])
        display_style = "block" if photo_index == 0 else "none"
        file_name = html.escape(photo["file"])
        time_text = html.escape(format_time(photo["taken_time"]))

        if image_uri:
            image_html = (
                f'<img src="{image_uri}" '
                'style="width: 260px; max-height: 190px; object-fit: contain; '
                'display: block; margin: 6px 0; border-radius: 4px;">'
            )
        else:
            image_html = (
                '<div style="width: 260px; padding: 20px 0; margin: 6px 0; '
                'text-align: center; background: #f2f2f2; color: #555; '
                'border-radius: 4px;">Photo preview unavailable</div>'
            )

        photo_slides.append(f"""
        <div class="{popup_id}-photo" style="display: {display_style};">
            {image_html}
            <div><b>{photo_index + 1}. {file_name}</b></div>
            <div>Time: {time_text}</div>
            <div>Lat: {photo['lat']:.6f}</div>
            <div>Lon: {photo['lon']:.6f}</div>
        </div>
        """)

    controls = ""
    if len(photos) > 1:
        controls = f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-top: 8px;">
            <button onclick="showSitePhoto('{popup_id}', -1)" style="cursor: pointer;">&lt;</button>
            <span id="{popup_id}-counter">1 / {len(photos)}</span>
            <button onclick="showSitePhoto('{popup_id}', 1)" style="cursor: pointer;">&gt;</button>
        </div>
        """

    return f"""
    <div style="width: 270px;">
        <b>{popup_title}</b><br>
        Photos: {len(photos)}<br>
        {"".join(photo_slides)}
        {controls}
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
            <span>Dham (धाम)</span>
        </div>
        <div style="display: flex; align-items: center; gap: 7px; margin: 2px 0; white-space: nowrap;">
            <span style="align-items: center; background: {JYOTIRLINGA_MARKER_COLOR}; border: 1px solid white; border-radius: 50% 50% 50% 0; box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.25); color: white; display: flex; height: 14px; justify-content: center; line-height: 14px; transform: rotate(-45deg); width: 14px;">
            </span>
            <span>Jyotirlingha (ज्योतिर्लिङ्ग)</span>
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
            legend.style.zIndex = "2147483647";
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
            title.style.zIndex = "2147483646";
            title.style.background = "rgba(255, 255, 255, 0.96)";
            title.style.border = "1px solid rgba(0, 0, 0, 0.3)";
            title.style.borderRadius = "4px";
            title.style.boxShadow = "0 1px 5px rgba(0, 0, 0, 0.25)";
            title.style.color = "#111";
            title.style.fontFamily = "Arial, sans-serif";
            title.style.fontSize = "15px";
            title.style.lineHeight = "24px";
            title.style.padding = "7px 14px";
            title.style.textAlign = "center";
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
    <script>
        window.sitePhotoIndexes = window.sitePhotoIndexes || {};

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
                max_width=320
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
