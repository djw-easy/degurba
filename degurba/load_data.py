import os
import zipfile
import tempfile
import urllib.request
from glob import glob
from .io import Raster, Vector


gpw_v4_unadjusted_1km = {
    "name": "Gridded Population of the World (GPW), v4  ( 30 arc-second )",
    "base_url": "https://sedac.ciesin.columbia.edu/downloads/data/gpw-v4/gpw-v4-population-count-rev11/gpw-v4-population-count-rev11_{year}_30_sec_tif.zip",
}

gpw_v4_adjusted_1km = {
    "name": "Gridded Population of the World (GPW), v4  ( 30 arc-second )",
    "base_url": "https://sedac.ciesin.columbia.edu/downloads/data/gpw-v4/gpw-v4-population-count-adjusted-to-2015-unwpp-country-totals-rev11/gpw-v4-population-count-adjusted-to-2015-unwpp-country-totals-rev11_2000_30_sec_tif.zip",
}

gpw_datasets = {
    'gpw_v4_unadjusted_1km': gpw_v4_unadjusted_1km,
    'gpw_v4_adjusted_1km': gpw_v4_adjusted_1km,
    "valid_years": [2000, 2005, 2010, 2015, 2020]
}

worldPop_unadjusted_1km = {
    "name": "Unconstrained individual countries 2000-2020  ( 1km resolution )",
    "base_url": "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/{year}/{country_upper}/{country_lower}_ppp_{year}_1km_Aggregated.tif"
}

worldPop_adjusted_1km = {
    "name": "Unconstrained individual countries 2000-2020 UN adjusted  ( 1km resolution )",
    "base_url": "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/{year}/{country_upper}/{country_lower}_ppp_{year}_1km_Aggregated_UNadj.tif"
}

wp_datasets = {
    'worldPop_unadjusted_1km': worldPop_unadjusted_1km,
    'worldPop_adjusted_1km': worldPop_adjusted_1km,
    "valid_years": list(range(2000, 2021))
}

wp_info = {"Algeria": "dza", "Angola": "ago", "Benin": "ben", "Botswana": "bwa", "Burkina Faso": "bfa", "Burundi": "bdi", "Cameroon": "cmr", "Cape Verde": "cpv",
           "Central African Republic": "caf", "Chad": "tcd", "Comoros": "com", "Congo": "cog", "Cote d'Ivoire": "civ", "Democratic Republic of the Congo": "cod",
           "Djibouti": "dji", "Egypt": "egy", "Equatorial Guinea": "gnq", "Eritrea": "eri", "Ethiopia": "eth", "Gabon": "gab", "Gambia": "gmb", "Ghana": "gha",
           "Guinea": "gin", "Guinea-Bissau": "gnb", "Kenya": "ken", "Lesotho": "lso", "Liberia": "lbr", "Libya": "lby", "Madagascar": "mdg", "Malawi": "mwi", "Mali": "mli",
           "Mauritania": "mrt", "Mauritius": "mus", "Mayotte": "myt", "Morocco": "mar", "Mozambique": "moz", "Namibia": "nam", "Niger": "ner", "Nigeria": "nga", "Réunion": "reu",
           "Rwanda": "rwa", "Saint Helena, Ascension and Tristan da Cunha": "shn", "Sao Tome and Principe": "stp", "Senegal": "sen", "Seychelles": "syc", "Sierra Leone": "sle",
           "Somalia": "som", "South Africa": "zaf", "South Sudan": "ssd", "Sudan": "sdn", "Swaziland": "swz", "Tanzania": "tza", "Togo": "tgo", "Tunisia": "tun", "Uganda": "uga",
           "Western Sahara": "esh", "Zambia": "zmb", "Zimbabwe": "zwe", "Anguilla": "aia", "Antigua and Barbuda": "atg", "Argentina": "arg", "Aruba": "abw", "Bahamas": "bhs",
           "Barbados": "brb", "Belize": "blz", "Bermuda": "bmu", "Bolivia": "bol", "Bonaire, Sint Eustatius and Saba": "bes", "Brazil": "bra", "British Virgin Islands": "vgb",
           "Canada": "can", "Cayman Islands": "cym", "Chile": "chl", "Colombia": "col", "Costa Rica": "cri", "Cuba": "cub", "Curaçao": "cuw", "Dominica": "dma", "Dominican Republic": "dom",
           "Ecuador": "ecu", "El Salvador": "slv", "Falkland Islands (Malvinas)": "flk", "French Guiana": "guf", "Greenland": "grl", "Grenada": "grd", "Guadeloupe": "glp", "Guatemala": "gtm",
           "Guyana": "guy", "Haiti": "hti", "Honduras": "hnd", "Jamaica": "jam", "Martinique": "mtq", "Mexico": "mex", "Montserrat": "msr", "Nicaragua": "nic", "Panama": "pan", "Paraguay": "pry",
           "Peru": "per", "Puerto Rico": "pri", "Saint Barthélemy": "blm", "Saint Kitts and Nevis": "kna", "Saint Lucia": "lca", "Saint Martin": "maf", "Saint Pierre and Miquelon": "spm",
           "Saint Vincent and the Grenadines": "vct", "Sint Maarten (Dutch part)": "sxm", "Suriname": "sur", "Trinidad and Tobago": "tto", "Turks and Caicos Islands": "tca", "United States of America": "50",
           "United States Virgin Islands": "vir", "Uruguay": "ury", "Venezuela": "ven", "Afghanistan": "afg", "Armenia": "arm", "Azerbaijan": "aze", "Bahrain": "bhr", "Bangladesh": "bgd", "Bhutan": "btn",
           "Brunei Darussalam": "brn", "Cambodia": "khm", "China": "chn", "Cyprus": "cyp", "Georgia": "geo", "Hong Kong": "hkg", "India": "ind", "Indonesia": "idn", "Iran": "irn", "Iraq": "irq",
           "Israel": "isr", "Japan": "jpn", "Jordan": "jor", "Kazakhstan": "kaz", "Kuwait": "kwt", "Kyrgyz Republic": "kgz", "Lao People's Democratic Republic": "lao", "Lebanon": "lbn", "Macao": "mac",
           "Malaysia": "mys", "Maldives": "mdv", "Mongolia": "mng", "Myanmar": "mmr", "Nepal": "npl", "North Korea": "prk", "Oman": "omn", "Pakistan": "pak", "Palestinian Territory": "pse", "Philippines": "phl",
           "Qatar": "qat", "Saudi Arabia": "sau", "Singapore": "sgp", "South Korea": "kor", "Sri Lanka": "lka", "Syrian Arab Republic": "syr", "Taiwan": "twn", "Tajikistan": "tjk", "Thailand": "tha", "Timor-Leste": "tls",
           "Turkey": "tur", "Turkmenistan": "tkm", "United Arab Emirates": "are", "Uzbekistan": "uzb", "Vietnam": "vnm", "Yemen": "yem", "Albania": "alb", "Andorra": "and", "Austria": "aut", "Belarus": "blr",
           "Belgium": "bel", "Bosnia and Herzegovina": "bih", "Bulgaria": "bgr", "Croatia": "hrv", "Czech Republic": "cze", "Denmark": "dnk", "Estonia": "est", "Faroe Islands": "fro", "Finland": "fin", "France": "fra",
           "Germany": "deu", "Gibraltar": "gib", "Greece": "grc", "Holy See (Vatican City State)": "vat", "Hungary": "hun", "Iceland": "isl", "Ireland": "irl", "Isle of Man": "imn", "Italy": "ita", "Latvia": "lva",
           "Liechtenstein": "lie", "Lithuania": "ltu", "Luxembourg": "lux", "Macedonia": "mkd", "Malta": "mlt", "Moldova": "mda", "Monaco": "mco", "Montenegro": "mne", "Netherlands": "nld", "Norway": "nor", "Poland": "pol",
           "Portugal": "prt", "Romania": "rou", "Russian Federation": "rus", "San Marino": "smr", "Serbia": "srb", "Slovakia (Slovak Republic)": "svk", "Slovenia": "svn", "Spain": "esp", "Sweden": "swe", "Switzerland": "che",
           "Ukraine": "ukr", "United Kingdom of Great Britain & Northern Ireland": "gbr", "American Samoa": "asm", "Australia": "aus", "Cook Islands": "cok", "Fiji": "fji", "French Polynesia": "pyf", "Guam": "gum",
           "Kiribati": "kir", "Marshall Islands": "mhl", "Micronesia": "fsm", "Nauru": "nru", "New Caledonia": "ncl", "New Zealand": "nzl", "Niue": "niu", "Northern Mariana Islands": "mnp", "Palau": "plw",
           "Papua New Guinea": "png", "Samoa": "wsm", "Solomon Islands": "slb", "Tokelau": "tkl", "Tonga": "ton", "Tuvalu": "tuv", "Vanuatu": "vut", "Wallis and Futuna": "wlf"}


class Dataset:
    _datasets = {
        'gpw_v4_unadjusted_1km',
        'gpw_v4_adjusted_1km',
        'worldPop_unadjusted_1km',
        'worldPop_adjusted_1km'
    }

    def __init__(
            self,
            ) -> None:
        pass

    def _find_url(self, dataset, year, country):
        country_upper, country_lower = None, None

        if dataset.startswith('worldPop'):
            country_lower = wp_info[country]
            print("The country that will be downloaded is {}".format(
                country))
            country_upper = country_lower.upper()
            if year not in wp_datasets['valid_years']:
                raise ValueError(
                    "The dataset {} in {} is not avaliable. ".format(dataset, year))

        if dataset.startswith('worldPop'):
            self.dataset = wp_datasets[dataset]
            self.url = self.dataset['base_url'].format(year=year, country_upper=country_upper,
                                                       country_lower=country_lower)
        elif dataset.startswith('gpw_v4'):
            self.dataset = gpw_datasets[dataset]
            self.url = self.dataset['base_url'].format(year=year)

    def _download(self, dataset) -> None:
        if dataset.startswith('worldPop'):
            try:
                urllib.request.urlretrieve(self.url, self.file_path)
            except urllib.error.ContentTooShortError:
                self._download()
        else:
            try:
                urllib.request.urlretrieve(self.url, self.fp.name)
            except urllib.error.ContentTooShortError:
                self._download()

    def download(
            self, 
            dataset,
            year,
            country=None,
            file_path=None
            ) -> None:
        """Download and load Population Counts Dataset.
            Args:
                dataset (string): dataset name to download.
                year: year of dataset to download.
                country: country of dataset to download, only needed when the dataset is worldpop.
        """
        year = int(year)
        if dataset not in self._datasets:
            raise ValueError(
                "The dataset {} is not avaliable. ".format(dataset))

        self._find_url(dataset=dataset, year=year, country=country)

        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            self.file_path = file_path
        else:
            raise ValueError("The path {} is not exist. ".format(file_path))

        if dataset.startswith('gpw_v4'):
            self.fp = tempfile.NamedTemporaryFile(suffix='.zip', mode='w', delete=False)

        print("Downloading " + os.path.basename(self.file_path) + " ... ")
        self._download(dataset)
        if dataset.startswith('gpw_v4'):
            z = zipfile.ZipFile(self.fp.name, 'r')
            target_dir = os.path.dirname(self.file_path)
            z.extract(path=target_dir)
            z.close()
            tif_path = glob(os.path.join(target_dir, '*.tif'))[0]
            os.rename(tif_path, self.file_path)
            self.fp.close()
        print('Done')

    def mask(self, shp: str):
        vector = Vector(shp)
        raster = Raster(self.file_path)
        raster = raster.read_from_geometry(vector.geometry)
        raster.save(self.file_path)
