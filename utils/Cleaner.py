import os
import shutil


def clearTemp():
    files = 0

    try:
        for filename in os.listdir("data/media/temp"):
            file = os.path.join("data/media/temp", filename)

            try:
                if os.path.isfile(file):
                    os.unlink(file)
                else:
                    shutil.rmtree(file)

                files += 1
            except Exception as e:
                print(f"Failed to clear temp, problem_file={file}, exception={e}")
        print(f"  ... Удалено {files} временных файлов")
    except:
        pass
