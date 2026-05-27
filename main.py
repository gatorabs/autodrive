import multiprocessing as mp

from src.presentation.ui.main_app import launch_application

def main():
    mp.set_start_method('spawn')

    with mp.Manager() as manager:
        launch_application(manager)

if __name__ == '__main__':
    main()
