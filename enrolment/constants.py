COMPANIES_HOUSE_COMPANY = 'companies-house-company'
NON_COMPANIES_HOUSE_COMPANY = 'non-companies-house-company'
NOT_COMPANY = 'not-company'
OVERSEAS_COMPANY = 'overseas-company'

# companies that have companies house numbers prefixed with below do not have address in companies house
COMPANY_NUMBER_PREFIXES_INCOMPLETE_INFO = (
    'IP',  # 'Industrial & Provident Company'
    'SP',  # 'Scottish Industrial/Provident Company'
    'IC',  # 'ICVC'
    'SI',  # 'Scottish ICVC'
    'RS',  # 'Registered Society'
    'NP',  # 'Northern Ireland Industrial/Provident Company or Credit Union'
    'NV',  # 'Northern Ireland ICVC'
    'RC',  # 'Royal Charter Company'
    'SR',  # 'Scottish Royal Charter Company'
    'NR',  # 'Northern Ireland Royal Charter Company'
    'CS',  # 'Scottish charitable incorporated organisation'
)
