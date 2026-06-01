import os
import json
import argparse
import math
import base64
import html
from io import BytesIO
from datetime import datetime
from PIL import Image, ExifTags
import folium

SITE_GROUP_RADIUS_KM = 0.5
THUMBNAIL_SIZE = (360, 260)


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

    return photo_infos


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


def photo_to_data_uri(image_path):
    try:
        with Image.open(image_path) as image:
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


def build_site_popup(site, site_number):
    photos = site["photos"]
    popup_id = f"site-{site_number}"
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
        <b>Site {site_number}</b><br>
        Photos: {len(photos)}<br>
        {"".join(photo_slides)}
        {controls}
    </div>
    """


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


def create_map(photo_infos, output_html, states_geojson=None):
    india_map = folium.Map(
        location=[22.5, 79.0],
        zoom_start=5,
        tiles="CartoDB positron"
    )
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

    # Add one marker per nearby-photo site.
    route_points = []
    sites = group_photos_by_site(photo_infos)

    for idx, site in enumerate(sites, start=1):
        lat, lon = site["center"]
        route_points.append([lat, lon])
        photo_count = len(site["photos"])
        first_file = site["photos"][0]["file"]
        tooltip = f"{idx}. {photo_count} photo"
        if photo_count != 1:
            tooltip += "s"
        tooltip += f" near {first_file}"

        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(build_site_popup(site, idx), max_width=320),
            tooltip=tooltip,
            icon=folium.Icon(color="red", icon="camera", prefix="fa")
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

        for start, end in zip(route_points, route_points[1:]):
            add_direction_arrow(india_map, start, end, 0.2)
            add_direction_arrow(india_map, start, end, 0.5)

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
