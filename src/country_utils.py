import pycountry

# Complete reference for all countries
ALL_COUNTRY_CODES = {country.alpha_3 for country in pycountry.countries}

CODE_TO_NAME = {country.alpha_3: country.name for country in pycountry.countries}

def get_missing_countries(df, year, code_col="Code", year_col="Year"):
    codes_in_year = set(df[df[year_col] == year][code_col].dropna())
    return list(ALL_COUNTRY_CODES - codes_in_year)