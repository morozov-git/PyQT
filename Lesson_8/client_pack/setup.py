from setuptools import setup, find_packages

setup(name="local_messenger_client_pack",
      version="0.0.1",
      description="local_messenger",
      author="Dmitry Morozov",
      author_email="morozov8943@yandex.ru",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )
