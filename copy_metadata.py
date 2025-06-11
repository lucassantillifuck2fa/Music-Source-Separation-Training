import argparse
from mutagen import File
from mutagen.flac import FLAC, Picture
from mutagen.id3 import ID3, APIC
from mutagen.mp4 import MP4, MP4Cover

# Mapping for MP3 ID3 to FLAC
id3_map = {
    "TIT2": "TITLE",
    "TPE1": "ARTIST",
    "TALB": "ALBUM",
    "TDRC": "DATE",
    "TCON": "GENRE",
    "TRCK": "TRACKNUMBER",
}

# Mapping for M4A (MP4) to FLAC
m4a_map = {
    "©nam": "TITLE",
    "©ART": "ARTIST",
    "©alb": "ALBUM",
    "©day": "DATE",
    "©gen": "GENRE",
    "trkn": "TRACKNUMBER",
}

def copy_cover_from_id3(source, target):
    for tag in source.tags.values():
        if isinstance(tag, APIC):
            pic = Picture()
            pic.data = tag.data
            pic.mime = tag.mime
            pic.type = 3  # Cover (front)
            target.clear_pictures()
            target.add_picture(pic)
            break

def copy_cover_from_mp4(source, target):
    if "covr" in source:
        cover = source["covr"][0]
        pic = Picture()
        pic.data = bytes(cover)
        pic.mime = "image/jpeg" if cover.imageformat == MP4Cover.FORMAT_JPEG else "image/png"
        pic.type = 3
        target.clear_pictures()
        target.add_picture(pic)

def copy_cover_from_flac(source, target):
    target.clear_pictures()
    for pic in source.pictures:
        target.add_picture(pic)

def copy_tags_with_mapping(source, target, mapping):
    for src_key, tgt_key in mapping.items():
        if src_key in source:
            value = source[src_key]
            if isinstance(value, list):
                # Convert each item in list to string, flatten tuples
                target[tgt_key] = [str(v[0]) if isinstance(v, tuple) else str(v) for v in value]
            else:
                target[tgt_key] = [str(value[0]) if isinstance(value, tuple) else str(value)]


def main():
    parser = argparse.ArgumentParser(description="Copy metadata from any audio file to a FLAC file")
    parser.add_argument("--source_file", required=True)
    parser.add_argument("--target_file", required=True)
    args = parser.parse_args()

    source = File(args.source_file)
    target = FLAC(args.target_file)

    # Clear existing metadata
    target.clear()
    target.clear_pictures()

    if isinstance(source, FLAC):
        for key in source.keys():
            target[key] = source[key]
        copy_cover_from_flac(source, target)

    elif isinstance(source.tags, ID3):
        copy_tags_with_mapping(source, target, id3_map)
        copy_cover_from_id3(source, target)

    elif isinstance(source, MP4):
        copy_tags_with_mapping(source, target, m4a_map)
        copy_cover_from_mp4(source, target)

    else:
        print("Unsupported source format.")
        return

    success = False
    title = target.get("TITLE", [""])[0]
    if title:
        target["TITLE"] = [title + " (Instrumental)"]
        success = True

    if success:
        print(f"Metadata copied from {args.source_file} to {args.target_file}")
    else:
        print("No metadata was copied.")

    target.save()
    
if __name__ == "__main__":
    main()
