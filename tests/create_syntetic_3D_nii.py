import numpy as np
import nibabel as nib
from scipy.ndimage import gaussian_filter


def create_synthetic_brain_nifti(output_filename='synthetic_brain.nii.gz', size=64):
    """
    יוצר קובץ NIfTI סינתטי קטן שמדמה סריקת T1 של מוח

    Parameters:
    output_filename: שם הקובץ הפלט
    size: גודל הנפח (ברירת מחדל 64x64x64 וקסלים)
    """

    # יצירת נפח ריק
    volume = np.zeros((size, size, size), dtype=np.float32)

    # יצירת כדור שמדמה את המוח
    center = size // 2
    radius = size // 3

    # יצירת מסכה כדורית
    x, y, z = np.ogrid[:size, :size, :size]
    mask = (x - center) ** 2 + (y - center) ** 2 + (z - center) ** 2 <= radius ** 2

    # מילוי עם ערכי עוצמה שמדמים רקמת מוח
    # חומר אפור: ~100-110
    # חומר לבן: ~120-130
    # CSF: ~20-30

    # יצירת שכבות בסיסיות
    volume[mask] = 100  # חומר אפור בסיסי

    # הוספת אזור פנימי של חומר לבן
    inner_radius = radius * 0.7
    inner_mask = (x - center) ** 2 + (y - center) ** 2 + (z - center) ** 2 <= inner_radius ** 2
    volume[inner_mask] = 125

    # הוספת חדרי מוח (ventricles) קטנים
    ventricle_radius = radius * 0.2
    ventricle_mask = (x - center) ** 2 + (y - center) ** 2 + (z - center) ** 2 <= ventricle_radius ** 2
    volume[ventricle_mask] = 25

    # הוספת רעש ריאליסטי
    noise = np.random.normal(0, 2, volume.shape)
    volume += noise

    # החלקה קלה כדי שייראה יותר ריאליסטי
    volume = gaussian_filter(volume, sigma=0.5)

    # הגבלת ערכים לטווח ריאליסטי
    volume = np.clip(volume, 0, 255)

    # יצירת affine transformation matrix
    # רזולוציה של 3mm x 3mm x 3mm (גדולה אבל מהירה לעיבוד)
    affine = np.eye(4)
    affine[0, 0] = 3.0
    affine[1, 1] = 3.0
    affine[2, 2] = 3.0
    affine[:3, 3] = -center * 3  # מרכוז הנפח

    # יצירת אובייקט NIfTI
    img = nib.Nifti1Image(volume, affine)

    # הוספת מטא-דאטה חשובים
    img.header['descrip'] = b'Synthetic T1 brain for testing'
    img.header['qform_code'] = 1
    img.header['sform_code'] = 1

    # שמירת הקובץ
    nib.save(img, output_filename)
    print(f"נוצר קובץ {output_filename} בהצלחה!")
    print(f"גודל: {size}x{size}x{size} וקסלים")
    print(f"רזולוציה: 3x3x3 מ\"מ")

    return output_filename


def create_minimal_brain():
    """יוצר מוח סינתטי מינימלי במיוחד (32x32x32)"""
    return create_synthetic_brain_nifti('minimal_brain.nii.gz', size=32)


def create_standard_test_brain():
    """יוצר מוח סינתטי בגודל סטנדרטי לבדיקות (64x64x64)"""
    return create_synthetic_brain_nifti('test_brain.nii.gz', size=64)


if __name__ == "__main__":
    # התקנת הספריות הנדרשות (אם עדיין לא מותקנות):
    # pip install nibabel numpy scipy

    # יצירת קובץ בדיקה קטן
    filename = create_minimal_brain()

    print("\nכדי להריץ FreeSurfer על הקובץ:")
    print(f"export SUBJECTS_DIR=/path/to/output/directory")
    print(f"recon-all -i {filename} -s test_subject -all")
    print("\nאו לבדיקה מהירה יותר:")
    print(f"recon-all -i {filename} -s test_subject -autorecon1")