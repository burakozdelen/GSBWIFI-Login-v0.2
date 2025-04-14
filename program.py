import requests
from bs4 import BeautifulSoup
import urllib3
import time
import os
import sys
import ctypes

# Konsol başlığını ayarla
ctypes.windll.kernel32.SetConsoleTitleW("GSBWIFI|Giriş Sistemi")

# SSL uyarılarını devre dışı bırak
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_credentials():
    # Exe'nin bulunduğu klasörü al
    exe_dir = os.path.dirname(os.path.abspath(__file__))
    credentials_file = os.path.join(exe_dir, 'credentials.txt')
    
    # Dosya yoksa oluştur
    if not os.path.exists(credentials_file):
        print("credentials.txt dosyası bulunamadı, oluşturuluyor...")
        try:
            with open(credentials_file, 'w') as file:
                file.write("username=TC\n")
                file.write("password=password")
            print(" credentials.txt dosyası oluşturuldu!")
        except Exception as e:
            print(f" Dosya oluşturma hatası: {str(e)}")
            input("Devam etmek için bir tuşa basın...")
            exit()
    
    try:
        with open(credentials_file, 'r') as file:
            credentials = {}
            for line in file:
                if '=' in line:
                    key, value = line.strip().split('=')
                    credentials[key] = value
            return credentials.get('username'), credentials.get('password')
    except Exception as e:
        print(f" Dosya okuma hatası: {str(e)}")
        input("Devam etmek için bir tuşa basın...")
        exit()

def logout_session(session):
    print("\n Servis durdurma işlemi başlatılıyor...")
    
    try:
        # Önce ana sayfayı yükle
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'tr,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Host': 'wifi.gsb.gov.tr',
            'Referer': 'https://wifi.gsb.gov.tr/index.html',
            'Upgrade-Insecure-Requests': '1'
        }
        
        session.headers.update(headers)
        index_response = session.get('https://wifi.gsb.gov.tr/index.html')
        
        if index_response.status_code == 200:
            print(" Ana sayfa yüklendi")
            
            soup = BeautifulSoup(index_response.text, 'html.parser')
            view_state = soup.find('input', {'name': 'javax.faces.ViewState'})['value']
            print(f"ViewState bulundu: {view_state}")
            
            # Durdur butonu için headers
            stop_headers = {
                'Accept': 'application/xml, text/xml, */*; q=0.01',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'Faces-Request': 'partial/ajax',
                'X-Requested-With': 'XMLHttpRequest',
                'Origin': 'https://wifi.gsb.gov.tr',
                'Pragma': 'no-cache',
                'Server': 'KYK Server'
            }
            
            session.headers.update(stop_headers)
            
            # Durdur butonu için data
            stop_data = {
                'servisUpdateForm': 'servisUpdateForm',
                'javax.faces.partial.ajax': 'true',
                'javax.faces.source': 'servisUpdateForm:j_idt161',
                'javax.faces.partial.execute': '@all',
                'javax.faces.partial.render': 'servisUpdateForm',
                'servisUpdateForm:j_idt161': 'servisUpdateForm:j_idt161',
                'javax.faces.ViewState': view_state
            }
            
            print("Servis durdurma isteği gönderiliyor...")
            stop_response = session.post(
                'https://wifi.gsb.gov.tr/index.html',
                data=stop_data
            )
            
            print(f"Debug - Stop Response Status: {stop_response.status_code}")
            print(f"Debug - Stop Response Headers: {dict(stop_response.headers)}")
            print(f"Debug - Stop Response Content: {stop_response.text[:200]}")
            
            if stop_response.status_code == 200:
                print(" Servis durdurma isteği gönderildi!")
                time.sleep(2)  # Sunucunun işlemi tamamlaması için bekle
                return True
            else:
                print(" Servis durdurma başarısız!")
                return False
        else:
            print(" Ana sayfa yüklenemedi!")
            return False
            
    except Exception as e:
        print(f" Hata oluştu: {str(e)}")
        return False

def login_session(username, password):
    print("\n Giriş işlemi başlatılıyor...")
    
    # Giriş için gerekli bilgiler
    login_url = 'https://wifi.gsb.gov.tr/j_spring_security_check'
    home_url = 'https://wifi.gsb.gov.tr/'
    
    # Headers ekle
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'tr,en-US;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    # Oturum için bir session oluşturuyoruz
    session = requests.Session()
    session.headers.update(headers)
    session.verify = False  # SSL doğrulamasını devre dışı bırak
    
    # Giriş formunu doldurmak için gerekli veriler
    login_data = {
        'j_username': username,
        'j_password': password,
        'submit': 'Giriş'
    }
    
    try:
        # Giriş isteği
        login_response = session.post(login_url, data=login_data, timeout=60)
        
        print(f"Debug - Response URL: {login_response.url}")
        print(f"Debug - Status Code: {login_response.status_code}")
        
        # Giriş başarılı mı kontrol et
        if login_response.status_code == 200:
            if "j_spring_security_check" not in login_response.url:
                print(" Giriş başarılı.")
                return session
            else:
                print(" Giriş başarısız. Kullanıcı adı veya şifre hatalı olabilir.")
                print(f"Debug - Response içeriği: {login_response.text[:200]}...")
                return None
        else:
            print(f" Giriş başarısız. Durum Kodu: {login_response.status_code}")
            return None
            
    except Exception as e:
        print(f" Hata oluştu: {str(e)}")
        return None

def cikis_yap(session):
    try:
        # Maksimum cihaz sayfasına git
        maksimum_cihaz_url = 'https://wifi.gsb.gov.tr/maksimumCihazHakkiDolu.html'
        maksimum_cihaz_response = session.get(maksimum_cihaz_url, timeout=60)

        if maksimum_cihaz_response.status_code == 200:
            soup = BeautifulSoup(maksimum_cihaz_response.text, 'html.parser')
            
            # ViewState değerini bul
            view_state_input = soup.find('input', {'name': 'javax.faces.ViewState'})
            if view_state_input:
                view_state = view_state_input.get('value')
                
                # Oturum sonlandırma isteği için headers
                ajax_headers = {
                    'faces-request': 'partial/ajax',
                    'x-requested-with': 'XMLHttpRequest',
                    'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                }
                session.headers.update(ajax_headers)
                
                # Sonlandırma isteği için form verileri
                logout_data = {
                    'javax.faces.partial.ajax': 'true',
                    'javax.faces.source': 'j_idt20:0:j_idt28:j_idt29',
                    'javax.faces.partial.execute': '@all',
                    'javax.faces.partial.render': '@all',
                    'j_idt20:0:j_idt28:j_idt29': 'j_idt20:0:j_idt28:j_idt29',
                    'j_idt20:0:j_idt28': 'j_idt20:0:j_idt28',
                    'javax.faces.ViewState': view_state
                }

                # Oturum sonlandırma isteği
                logout_response = session.post(
                    maksimum_cihaz_url,
                    data=logout_data,
                    timeout=60
                )
                
                if logout_response.status_code == 200:
                    print("Oturum sonlandırma isteği gönderildi.")
                    print(f"Debug - Logout Response: {logout_response.text[:200]}...")
                    
                    # 2 saniye bekle
                    time.sleep(2)
                    
                    # Çıkış URL'sine yönlendir
                    final_logout = session.get('https://wifi.gsb.gov.tr/logout', timeout=60)
                    
                    if final_logout.status_code in [302, 200]:
                        print(" Oturum başarıyla sonlandırıldı.")
                    return True
        
        print(" Çıkış yapılırken hata oluştu")
        return False
    except Exception as e:
        print(f" Çıkış hatası: {str(e)}")
        return False

def main():
    while True:
        print("\n=== GSBWIFI Giriş Sistemi ===")
        print("1. Giriş Yap")
        print("2. Oturumu Sonlandır")
        print("3. Çıkış")
        
        choice = input("\nSeçiminiz (1-3): ")
        
        if choice == "1":
            try:
                print(" Giriş yapılıyor...")
                # SSL uyarılarını devre dışı bırak
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

                # Kullanıcı bilgilerini dosyadan oku veya oluştur
                def get_credentials():
                    credentials_file = 'credentials.txt'
                    
                    # Dosya yoksa oluştur
                    if not os.path.exists(credentials_file):
                        print(" credentials.txt dosyası bulunamadı, oluşturuluyor...")
                        try:
                            with open(credentials_file, 'w') as file:
                                file.write("username=TC\n")
                                file.write("password=password")
                            print(" credentials.txt dosyası oluşturuldu!")
                        except Exception as e:
                            print(f" Dosya oluşturma hatası: {str(e)}")
                            return None, None
                    
                    # Dosyayı oku
                    try:
                        with open(credentials_file, 'r') as file:
                            credentials = {}
                            for line in file:
                                if '=' in line:
                                    key, value = line.strip().split('=')
                                    credentials[key] = value
                            return credentials.get('username'), credentials.get('password')
                    except Exception as e:
                        print(f" Dosya okuma hatası: {str(e)}")
                        return None, None

                # Kullanıcı bilgilerini al
                username, password = get_credentials()

                if not username or not password:
                    print(" Kullanıcı adı veya şifre bulunamadı!")
                    continue

                # Giriş için gerekli bilgiler
                login_url = 'https://wifi.gsb.gov.tr/j_spring_security_check'
                home_url = 'https://wifi.gsb.gov.tr/'

                # Headers ekle
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'tr,en-US;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }

                # Oturum için bir session oluşturuyoruz
                session = requests.Session()
                session.headers.update(headers)
                session.verify = False  # SSL doğrulamasını devre dışı bırak

                # Giriş formunu doldurmak için gerekli veriler
                login_data = {
                    'j_username': username,
                    'j_password': password,
                    'submit': 'Giriş'
                }

                # Giriş isteği
                login_response = session.post(login_url, data=login_data, timeout=60)

                # Giriş başarılı mı kontrol et (daha detaylı kontrol)
                if login_response.status_code == 200:
                    if "j_spring_security_check" not in login_response.url:
                        print(" Giriş yapılma işlemi devam ediyor...")
                    else:
                        print(" Giriş başarısız. Kullanıcı adı veya şifre hatalı olabilir.")
                        continue
                else:
                    print(f" Giriş başarısız. Durum Kodu: {login_response.status_code}")
                    continue

                # Maksimum cihaz sayfasına yönlendirildiyse
                maksimum_cihaz_url = 'https://wifi.gsb.gov.tr/maksimumCihazHakkiDolu.html'
                maksimum_cihaz_response = session.get(maksimum_cihaz_url, timeout=60)

                if maksimum_cihaz_response.status_code == 200:
                    soup = BeautifulSoup(maksimum_cihaz_response.text, 'html.parser')
                    
                    # ViewState değerini bul
                    view_state_input = soup.find('input', {'name': 'javax.faces.ViewState'})
                    if view_state_input:
                        view_state = view_state_input.get('value')
                        
                        # Oturum sonlandırma isteği için headers
                        ajax_headers = {
                            'faces-request': 'partial/ajax',
                            'x-requested-with': 'XMLHttpRequest',
                            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        }
                        session.headers.update(ajax_headers)
                        
                        # Sonlandırma isteği için form verileri
                        logout_data = {
                            'javax.faces.partial.ajax': 'true',
                            'javax.faces.source': 'j_idt20:0:j_idt28:j_idt29',
                            'javax.faces.partial.execute': '@all',
                            'javax.faces.partial.render': '@all',
                            'j_idt20:0:j_idt28:j_idt29': 'j_idt20:0:j_idt28:j_idt29',
                            'j_idt20:0:j_idt28': 'j_idt20:0:j_idt28',
                            'javax.faces.ViewState': view_state
                        }

                        # Önce oturum sonlandırma isteği
                        logout_response = session.post(
                            maksimum_cihaz_url,
                            data=logout_data,
                            timeout=60
                        )
                        
                        if logout_response.status_code == 200:
                            # Çıkış URL'sine yönlendir
                            final_logout = session.get('https://wifi.gsb.gov.tr/logout', timeout=60)
                            
                            # 302 veya 200 status code'unu kabul et
                            if final_logout.status_code in [302, 200]:
                                # 3 saniye bekle
                                time.sleep(3)
                                
                                # Yeniden giriş yap
                                session.headers.update(headers)  # Ajax headers'ı temizle
                                login_response = session.post(login_url, data=login_data, timeout=60)
                                
                                if login_response.status_code == 200 and "maksimumCihazHakkiDolu.html" not in login_response.url:
                                    print(" Giriş başarılı!")
                                else:
                                    print(" Giriş başarısız oldu.")
                            else:
                                print(" Oturum sonlandırma başarısız oldu.")
                        else:
                            print(" Oturum sonlandırma isteği başarısız.")
                    else:
                        print(" ViewState değeri bulunamadı.")
                else:
                    print(" Maksimum cihaz sayfasına erişilemedi.")
            except requests.exceptions.RequestException as e:
                print(" Bağlantı hatası oluştu. Lütfen internet bağlantınızı kontrol ediniz.")
            except Exception as e:
                print(" Beklenmeyen bir hata oluştu. Lütfen tekrar deneyiniz.")

        elif choice == "2":
            try:
                # SSL uyarılarını devre dışı bırak
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                print(" Oturum sonlandırılıyor...")
                # Kullanıcı bilgilerini dosyadan oku veya oluştur
                def get_credentials():
                    credentials_file = 'credentials.txt'
                    
                    # Dosya yoksa oluştur
                    if not os.path.exists(credentials_file):
                        print("credentials.txt dosyası bulunamadı, oluşturuluyor...")
                        try:
                            with open(credentials_file, 'w') as file:
                                file.write("username=TC\n")
                                file.write("password=password")
                            print(" credentials.txt dosyası oluşturuldu!")
                        except Exception as e:
                            print(f" Dosya oluşturma hatası: {str(e)}")
                            return None, None
                    
                    # Dosyayı oku
                    try:
                        with open(credentials_file, 'r') as file:
                            credentials = {}
                            for line in file:
                                if '=' in line:
                                    key, value = line.strip().split('=')
                                    credentials[key] = value
                            return credentials.get('username'), credentials.get('password')
                    except Exception as e:
                        print(f" Dosya okuma hatası: {str(e)}")
                        return None, None

                # Kullanıcı bilgilerini al
                username, password = get_credentials()

                if not username or not password:
                    print(" Kullanıcı adı veya şifre bulunamadı!")
                    continue

                # Giriş için gerekli bilgiler
                login_url = 'https://wifi.gsb.gov.tr/j_spring_security_check'
                home_url = 'https://wifi.gsb.gov.tr/'

                # Headers ekle
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'tr,en-US;q=0.9,en;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                }

                # Oturum için bir session oluşturuyoruz
                session = requests.Session()
                session.headers.update(headers)
                session.verify = False  # SSL doğrulamasını devre dışı bırak

                # Giriş formunu doldurmak için gerekli veriler
                login_data = {
                    'j_username': username,
                    'j_password': password,
                    'submit': 'Giriş'
                }

                # Giriş isteği
                login_response = session.post(login_url, data=login_data, timeout=60)

                # Giriş başarılı mı kontrol et (daha detaylı kontrol)
                if login_response.status_code == 200:
                    if "j_spring_security_check" not in login_response.url:
                        print(" Oturum sonlandırma işlemi devam ediyor...")
                    else:
                        print(" Çıkış başarısız. Kullanıcı adı veya şifre hatalı olabilir.")
                        continue
                else:
                    print(f" Çıkış başarısız. Durum Kodu: {login_response.status_code}")
                    continue

                # Maksimum cihaz sayfasına yönlendirildiyse
                maksimum_cihaz_url = 'https://wifi.gsb.gov.tr/maksimumCihazHakkiDolu.html'
                maksimum_cihaz_response = session.get(maksimum_cihaz_url, timeout=60)

                if maksimum_cihaz_response.status_code == 200:
                    soup = BeautifulSoup(maksimum_cihaz_response.text, 'html.parser')
                    
                    # ViewState değerini bul
                    view_state_input = soup.find('input', {'name': 'javax.faces.ViewState'})
                    if view_state_input:
                        view_state = view_state_input.get('value')
                        
                        # Oturum sonlandırma isteği için headers
                        ajax_headers = {
                            'faces-request': 'partial/ajax',
                            'x-requested-with': 'XMLHttpRequest',
                            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                        }
                        session.headers.update(ajax_headers)
                        
                        # Sonlandırma isteği için form verileri
                        logout_data = {
                            'javax.faces.partial.ajax': 'true',
                            'javax.faces.source': 'j_idt20:0:j_idt28:j_idt29',
                            'javax.faces.partial.execute': '@all',
                            'javax.faces.partial.render': '@all',
                            'j_idt20:0:j_idt28:j_idt29': 'j_idt20:0:j_idt28:j_idt29',
                            'j_idt20:0:j_idt28': 'j_idt20:0:j_idt28',
                            'javax.faces.ViewState': view_state
                        }

                        # Önce oturum sonlandırma isteği
                        logout_response = session.post(
                            maksimum_cihaz_url,
                            data=logout_data,
                            timeout=60
                        )
                        
                        if logout_response.status_code == 200:
                            # 2 saniye bekle
                            time.sleep(2)
                            
                            # Çıkış URL'sine yönlendir
                            final_logout = session.get('https://wifi.gsb.gov.tr/logout', timeout=60)
                            
                            if final_logout.status_code in [302, 200]:
                                print(" Oturum başarıyla sonlandırıldı.")
                        else:
                            print(" Oturum sonlandırma isteği başarısız.")
                    else:
                        print(" ViewState değeri bulunamadı.")
                else:
                    print(" Maksimum cihaz sayfasına erişilemedi.")
            except requests.exceptions.RequestException as e:
                print(" Bağlantı hatası oluştu. Lütfen internet bağlantınızı kontrol ediniz.")
            except Exception as e:
                print(" Beklenmeyen bir hata oluştu. Lütfen tekrar deneyiniz.")

        elif choice == "3":
            print("\nProgram kapatılıyor...")
            sys.exit()

        else:
            print("\n Geçersiz seçim! Lütfen 1-3 arasında bir sayı girin.")
        
        input("\nDevam etmek için bir tuşa basın...")

if __name__ == "__main__":
    main()