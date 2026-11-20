import os
import shutil
from pathlib import Path

# Extension ते Category मॅपिंग
EXTENSION_MAP = {
    ".pdf": "Documents",
    ".doc": "Documents",
    ".docx": "Documents",
    ".txt": "Documents",
    ".csv": "Documents",
    ".xlsx": "Documents",
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".gif": "Images",
    ".mp4": "Videos",
    ".mkv": "Videos",
    ".avi": "Videos",
    ".zip": "Archives",
    ".rar": "Archives",
    ".tar": "Archives",
    ".py": "Code",
    ".js": "Code",
    ".html": "Code",
    ".css": "Code",
}


def get_unique_destination(dest_folder, filename):
  """जर त्याच नावाची फाइल आधीच असेल तर नाव बदलून (उदा. file_1.pdf) देतो."""
  base_path = Path(dest_folder) / filename
  if not base_path.exists():
    return base_path

  stem = base_path.stem
  suffix = base_path.suffix
  counter = 1
  while True:
    new_path = Path(dest_folder) / f"{stem}_{counter}{suffix}"
    if not new_path.exists():
      return new_path
    counter += 1


def organize_directory(target_dir):
  target_path = Path(target_dir)
  if not target_path.exists() or not target_path.is_dir():
    print(f"[Error] '{target_dir}' हा फोल्डर सापडला नाही.")
    return

  summary = {}
  skipped = 0

  print(f"\nScanning directory: {target_path}\n" + "-" * 50)

  with os.scandir(target_path) as entries:
    for entry in entries:
      # फक्त फाइल्स तपासा, फोल्डर्स आणि स्वतः organizer.py ला हात लावू नका
      if not entry.is_file() or entry.name == "organizer.py":
        continue

      ext = Path(entry.name).suffix.lower()
      category = EXTENSION_MAP.get(ext, "Others")
      dest_folder = target_path / category

      try:
        # गरज असेल तरच नवीन फोल्डर तयार करा
        dest_folder.mkdir(exist_ok=True)
        dest_file = get_unique_destination(dest_folder, entry.name)

        shutil.move(entry.path, str(dest_file))
        print(f"[Moved] {entry.name}  --->  /{category}/{dest_file.name}")
        summary[category] = summary.get(category, 0) + 1

      except PermissionError:
        print(f"[Skipped - Permission Error] '{entry.name}' दुसऱ्या प्रोग्रॅममध्ये उघडी आहे.")
        skipped += 1
      except FileExistsError:
        print(f"[Skipped - File Exists] '{entry.name}' आधीच अस्तित्वात आहे.")
        skipped += 1
      except Exception as e:
        print(f"[Error] '{entry.name}' हलवताना अडचण आली: {e}")
        skipped += 1

  # Execution Summary प्रिंट करणे
  print("\n" + "=" * 50)
  print("            EXECUTION SUMMARY")
  print("=" * 50)
  total_moved = sum(summary.values())
  if total_moved == 0:
    print("हलवण्यासाठी कोणतीही नवीन फाइल सापडली नाही.")
  else:
    for cat, count in summary.items():
      print(f"  /{cat:<15} : {count} file(s)")
  print("-" * 50)
  print(f"Total Files Relocated : {total_moved}")
  print(f"Skipped / Errors      : {skipped}")
  print("=" * 50)


if __name__ == "__main__":
  print("=" * 50)
  print("     AUTOMATED FILE ORGANIZER & CLEANUP")
  print("=" * 50)
  user_input = input(
      "Organize करायच्या फोल्डरचा Path टाका (सध्याच्या फोल्डरसाठी Enter दाबा): "
  ).strip()

  folder_to_clean = (
      user_input if user_input else os.path.dirname(os.path.abspath(__file__))
  )
  organize_directory(folder_to_clean)