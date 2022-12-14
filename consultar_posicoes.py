import requests
import pandas as pd



### FUNÇÃO PARA PEGAR TOKEN DE AUTENTICAÇÃO NA API
def get_token(email,senha):
    ## BODY PARA REQUISIÇÃO NA API
    body = {"email": email,"password": senha}
    
    ## CHAMADA NA API
    r = requests.post('https://api.oplab.com.br/v3/domain/users/authenticate',json=body).json()['access-token']
    return r

### FUNÇÃO PARA CALCULAR GREGAS
def gregas(token,symbol):
    r = requests.get('https://api.oplab.com.br/v3/market/options/bs?symbol={}&irate=13,75'.format(symbol),headers={"Access-Token": token})
    return r.json()

### FUNÇÃO PARA CONSULTAR INFO DOS INSTRUMENTOS (CNPJ, ISIN)
def consult_instr(token,symbol):   
    r = requests.get('https://api.oplab.com.br/v3/market/instruments/{}'.format(symbol), headers={"Access-Token": token})
    return r.json()

### FUNÇÃO COLETAR E TRATAR POSIÇOES ABERTAS
def get_posicoes(token,nome_estrategia = 'TODAS'):
    port_id = requests.get("https://api.oplab.com.br/v3/domain/portfolios", headers={"Access-Token": token}).json()
    port_default = 0
    for i in port_id:
        if i['is_default'] == True:
            port_default = i['id']   
    r = requests.get('https://api.oplab.com.br/v3/domain/portfolios/{}/positions'.format(port_default), json = {'status':'open'},headers={"Access-Token": token}).json()
    ativo = []
    underlying = []
    strike = []
    vencimento = []
    preco_spot = []
    preco_medio = []
    bid = []
    ask = []
    amount = []
    delta = []
    tipo = []
    isin = []
    cnpj = []
    for i in r:
        if i['strategy'] == None:
            continue
        if i['strategy']['name'] == nome_estrategia or nome_estrategia == 'TODAS':
            vcto = i['info']['days_to_maturity'] if i['type'] == 'option' else 999
            if vcto <= 1:
                continue
            if i['amount'] == 0 or (i['type'] != 'stock' and i['type'] != 'option' and i['type'] != 'etf'):
                continue
            und = i['underlying_asset']['symbol'] if i['type'] == 'option' else i['symbol']
            info_und = consult_instr(token,und)
            bid.append(i['market']['bid'])
            ask.append(i['market']['ask'])
            tipo.append(i['info']['category'])
            ativo.append(i['symbol'] )
            underlying.append(und)
            strike.append(i['info']['strike'] if i['type'] == 'option' else i['market']['close'])
            vencimento.append(vcto)
            preco_spot.append(i['underlying_asset']['market']['close'] if i['type'] == 'option' else i['market']['close'])
            preco_medio.append(i['average_price'])
            delta.append(gregas(token,i['symbol'])['delta'] if i['type'] == 'option' else 1)
            amount.append(i['amount'])
            isin.append(info_und['isin'])
            cnpj.append(info_und['cnpj'])
        else:
            continue
            # print('O ativo {} não pôde ser incluído'.format(i['symbol']))
    df = pd.DataFrame({'tipo':tipo,'ativo':ativo,'spot':underlying,'strike':strike,'vcto':vencimento,'p_spot':preco_spot,'p_medio':preco_medio,'qtde':amount,'delta':delta,'bid':bid,'ask':ask,'isin':isin,'cnpj':cnpj})
    return df


### INSERIR EMAIL E SENHA --> get_token('seu@email.com','sua_senha')
try:
    token = get_token()
    # print(token)
except:
    print('TOKEN ERRADO')
    exit()

### 'C:/sua_pasta/
file_adress = 'C:/' 
if file_adress == '':
    print('INDICAR PASTA')
    exit()

df = get_posicoes(token,'TODAS')
df.to_excel(file_adress+'posicoes_oplab.xls')
print(df)
