import datetime
import hashlib
import os


def build_filename(year, month, day, feed_name, id, stripped=False):
    return (
        f"{year}-{month:02}-{day:02}"
        + f"-{feed_name}"
        + f"-{hashlib.sha256(id.encode()).hexdigest()}"
        + ("-stripped" if stripped else "")
        + ".mp3"
    )


def get_stripped_name(version, filename):
    if filename.endswith("-stripped.mp3"):
        raise ValueError(f"mp3 filename already stripped: {filename}")

    if filename.endswith(".mp3"):
        return f"{filename[:-4]}-stripped.{version}.mp3"

    raise ValueError(f"Invalid mp3 filename for adding stripped name: {filename}")


def is_stripped_filename(filename):
    return filename.split('.')[0].endswith("-stripped")


def matches_stripped_filename(filename, stripped_candidate):
    return stripped_candidate.split('.')[0].endswith(filename.split('.')[0] + "-stripped")


def get_version_number(path):
    directory, filename = os.path.split(path)
    parts = filename.split('.')
    if len(parts) < 3:
        return None
    return '.'.join(parts[1:-1])


def get_without_version_number(path):
    directory, filename = os.path.split(path)
    parts = filename.split('.')
    return os.path.join(directory, f'{parts[0]}.{parts[-1]}')


def find_stripped_filename(filename, candidates):
    if filename.endswith("-stripped.mp3"):
        return None

    versionless_candidates = [get_without_version_number(candidate) for candidate in candidates]

    versionless_filename = get_without_version_number(filename)
    for index, versionless_candidate in enumerate(versionless_candidates):
        if versionless_candidate.endswith(versionless_filename[:-4] + '-stripped.mp3'):
            return candidates[index]

    return None


def is_old(filename, since):
    published_str = "-".join(filename.split("-")[:3])
    try:
        published = datetime.datetime.strptime(published_str, "%Y-%m-%d")
    except ValueError as error:
        print(f'Failed to parse date in {filename}: {error}')
        return False

    if published >= since:
        return False

    return True


def get_day(path):
    directory, filename = os.path.split(path)
    parts = filename.split('-')
    return datetime.datetime(
            year=int(parts[0]),
            month=int(parts[1]),
            day=int(parts[2])
    )


def oldest_first(paths):
    return sorted(paths, key=get_day)
