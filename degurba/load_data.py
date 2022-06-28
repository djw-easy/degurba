import os
import urllib.request
import difflib


gpw_v4 = {
    "name": "Gridded Population of the World (GPW), v4  ( 30 arc-second )",
    "base_url": "https://sedac.ciesin.columbia.edu/downloads/data/gpw-v4/gpw-v4-population-count-rev11/gpw-v4-population-count-rev11_{year}_30_sec_tif.zip",
    "valid_years": [2000, 2005, 2010, 2015, 2020]
}

worldPop_unadjusted = {
    "name": "Unconstrained individual countries 2000-2020  ( 1km resolution )",
    "base_url": "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km/{year}/{country_upper}/{country_lower}_ppp_{year}_1km_Aggregated.tif",
    "valid_years": list(range(2000, 2021))
}

worldPop_adjusted = {
    "name": "Unconstrained individual countries 2000-2020 UN adjusted  ( 1km resolution )",
    "base_url": "https://data.worldpop.org/GIS/Population/Global_2000_2020_1km_UNadj/{year}/{country_upper}/{country_lower}_ppp_{year}_1km_Aggregated_UNadj.tif",
    "valid_years": list(range(2000, 2021))
}

wp_info = {"Algeria": "dza", "Angola": "ago", "Benin": "ben", "Botswana": "bwa", "Burkina Faso": "bfa", "Burundi": "bdi", "Cameroon": "cmr", "Cape Verde": "cpv",
           "Central African Republic": "caf", "Chad": "tcd", "Comoros": "com", "Congo": "cog", "Cote d'Ivoire": "civ", "Democratic Republic of the Congo": "cod",
           "Djibouti": "dji", "Egypt": "egy", "Equatorial Guinea": "gnq", "Eritrea": "eri", "Ethiopia": "eth", "Gabon": "gab", "Gambia": "gmb", "Ghana": "gha",
           "Guinea": "gin", "Guinea-Bissau": "gnb", "Kenya": "ken", "Lesotho": "lso", "Liberia": "lbr", "Libya": "lby", "Madagascar": "mdg", "Malawi": "mwi", "Mali": "mli",
           "Mauritania": "mrt", "Mauritius": "mus", "Mayotte": "myt", "Morocco": "mar", "Mozambique": "moz", "Namibia": "nam", "Niger": "ner", "Nigeria": "nga", "R\u00e9union": "reu",
           "Rwanda": "rwa", "Saint Helena, Ascension and Tristan da Cunha": "shn", "Sao Tome and Principe": "stp", "Senegal": "sen", "Seychelles": "syc", "Sierra Leone": "sle",
           "Somalia": "som", "South Africa": "zaf", "South Sudan": "ssd", "Sudan": "sdn", "Swaziland": "swz", "Tanzania": "tza", "Togo": "tgo", "Tunisia": "tun", "Uganda": "uga",
           "Western Sahara": "esh", "Zambia": "zmb", "Zimbabwe": "zwe", "Anguilla": "aia", "Antigua and Barbuda": "atg", "Argentina": "arg", "Aruba": "abw", "Bahamas": "bhs",
           "Barbados": "brb", "Belize": "blz", "Bermuda": "bmu", "Bolivia": "bol", "Bonaire, Sint Eustatius and Saba": "bes", "Brazil": "bra", "British Virgin Islands": "vgb",
           "Canada": "can", "Cayman Islands": "cym", "Chile": "chl", "Colombia": "col", "Costa Rica": "cri", "Cuba": "cub", "Cura\u00e7ao": "cuw", "Dominica": "dma", "Dominican Republic": "dom",
           "Ecuador": "ecu", "El Salvador": "slv", "Falkland Islands (Malvinas)": "flk", "French Guiana": "guf", "Greenland": "grl", "Grenada": "grd", "Guadeloupe": "glp", "Guatemala": "gtm",
           "Guyana": "guy", "Haiti": "hti", "Honduras": "hnd", "Jamaica": "jam", "Martinique": "mtq", "Mexico": "mex", "Montserrat": "msr", "Nicaragua": "nic", "Panama": "pan", "Paraguay": "pry",
           "Peru": "per", "Puerto Rico": "pri", "Saint Barth\u00e9lemy": "blm", "Saint Kitts and Nevis": "kna", "Saint Lucia": "lca", "Saint Martin": "maf", "Saint Pierre and Miquelon": "spm",
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
    """
        Args:
            process_dir (string): output dir of intermediate files or downloaded dataset.
            file_path (string): Raster file of Population Counts.
    """
    _datasets = {
        'gpw_v4': gpw_v4,
        'worldPop_unadjusted': worldPop_unadjusted,
        'worldPop_adjusted': worldPop_adjusted
    }

    def __init__(
            self,
            process_dir: str,
            file_path: str = None,
            ) -> None:
        
        if file_path != None:
            if os.path.exists(file_path):
                self.file_path = file_path
                return 
            else:
                raise ValueError("The path {} is not exist. ".format(file_path))
        self.process_dir = process_dir

    def _download(self) -> None:
        file_name = os.path.basename(self.url)
        self.file_path = os.path.join(
            self.process_dir, file_name)

        if os.path.exists(self.file_path):
            raise ValueError("File {} is already exist. ".format(file_name))

        print("Downloading " + file_name + " ... ")
        urllib.request.urlretrieve(self.url, self.file_path)
        print("Done")

    def download(
            self, 
            dataset: str = 'worldPop_adjusted',
            year: int = 2020,
            country: str = None
            ) -> None:
        """Download and load Population Counts Dataset.
            Args:
                dataset (string): dataset name to download.
                year: year of dataset to download.
                country: country of dataset to download, only needed when the dataset is worldpop.
        """
        if dataset not in self._datasets.keys():
            raise ValueError(
                "The dataset {} is not avaliable. ".format(dataset))

        if year not in self._datasets[dataset].valid_years:
            raise ValueError(
                "The dataset {} in {} is not avaliable. ".format(dataset, year))

        if dataset.startswith('worldPop'):
            if country == None:
                raise ValueError(
                    "The argparse country is needed when the dataset is worldpop.")
            else:
                match = difflib.get_close_matches(country, wp_info.keys(), n=1)
                if match:
                    country_upper = match[0]
                    country_lower = wp_info[country_upper]
                    print("The country that will be downloaded is {}".format(
                        country_upper))
                else:
                    raise ValueError(
                        "The country {} is not avaliable, avaliable country can be seen in https://hub.worldpop.org/geodata/listing?id=75. ".format(country))

        base_url = self._datasets[dataset]["base_url"]
        self.url = base_url.format(
            year=year, country_upper=country_upper, country_lower=country_lower)
        self.name = self._datasets[dataset]["base_url"] + ' in {}'.format(year)
        self._download()

    def mask(self, mask):
        pass