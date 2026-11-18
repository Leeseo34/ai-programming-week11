import pytest

from load_scores import load_scores


def test_정상_csv의_유효한_줄을_이름과_점수로_반환한다(tmp_path):
    csv_file = tmp_path / "scores.csv"
    csv_file.write_text(
        "name,score\n김하나,88\n이두리,72\n",
        encoding="utf-8",
    )

    kept, skipped = load_scores(str(csv_file))

    assert kept == [("김하나", 88), ("이두리", 72)]
    assert skipped == []


def test_존재하지_않는_파일은_FileNotFoundError를_발생시킨다(tmp_path):
    missing_file = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        load_scores(str(missing_file))


def test_헤더만_있으면_빈_결과와_빈_건너뛴_목록을_반환한다(tmp_path):
    csv_file = tmp_path / "header_only.csv"
    csv_file.write_text("name,score\n", encoding="utf-8")

    kept, skipped = load_scores(str(csv_file))

    assert kept == []
    assert skipped == []


def test_빈_파일도_멈추지_않고_빈_결과를_반환한다(tmp_path):
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("", encoding="utf-8")

    kept, skipped = load_scores(str(csv_file))

    assert kept == []
    assert skipped == []


def test_헤더가_없으면_첫_줄을_데이터로_처리한다(tmp_path):
    csv_file = tmp_path / "missing_header.csv"
    csv_file.write_text(
        "홍길동,90\n김철수,80\n",
        encoding="utf-8",
    )

    kept, skipped = load_scores(str(csv_file))

    assert kept == [("홍길동", 90), ("김철수", 80)]
    assert skipped == []


@pytest.mark.parametrize("header", ["score,name", "이름,성적", "name"])
def test_올바르지_않은_헤더는_실패로_보고한다(tmp_path, header):
    csv_file = tmp_path / "bad_header.csv"
    csv_file.write_text(
        f"{header}\n홍길동,90\n",
        encoding="utf-8",
    )

    kept, skipped = load_scores(str(csv_file))

    assert kept == []
    assert (1, header, "헤더가 올바르지 않음") in skipped


def test_열_개수가_두개가_아니면_줄번호_원본_이유와_함께_건너뛴다(tmp_path):
    csv_file = tmp_path / "bad_columns.csv"
    csv_file.write_text(
        "name,score\n장미르,72,비고없음\n김하나\n",
        encoding="utf-8",
    )

    kept, skipped = load_scores(str(csv_file))

    assert kept == []
    assert skipped == [
        (2, "장미르,72,비고없음", "열 개수가 2가 아님"),
        (3, "김하나", "열 개수가 2가 아님"),
    ]


@pytest.mark.parametrize(
    ("row", "reason"),
    [
        (",90", "이름이 비어 있음"),
        ("이두리,", "점수가 비어 있음"),
        ("박세찬,결석", "점수가 정수가 아님"),
        ("정오름,-1", "점수가 0~100 밖"),
        ("윤보람,101", "점수가 0~100 밖"),
    ],
)
def test_예외_데이터를_건너뛰고_이유를_보고한다(tmp_path, row, reason):
    csv_file = tmp_path / "invalid.csv"
    csv_file.write_text(f"name,score\n{row}\n", encoding="utf-8")

    kept, skipped = load_scores(str(csv_file))

    assert kept == []
    assert skipped == [(2, row, reason)]


@pytest.mark.parametrize(
    ("score", "kept"),
    [
        (0, True),
        (1, True),
        (99, True),
        (100, True),
        (-1, False),
        (101, False),
    ],
)
def test_점수는_0에서_100까지_허용한다(tmp_path, score, kept):
    csv_file = tmp_path / "boundary.csv"
    csv_file.write_text(
        f"name,score\n홍길동,{score}\n",
        encoding="utf-8",
    )

    result, skipped = load_scores(str(csv_file))

    assert (len(result) == 1) is kept
    if kept:
        assert skipped == []
    else:
        assert len(skipped) == 1
        assert skipped[0][2] == "점수가 0~100 밖"


def test_중복된_이름은_동명이인일_수_있으므로_둘_다_보존한다(tmp_path):
    csv_file = tmp_path / "duplicate.csv"
    csv_file.write_text(
        "name,score\n김하나,88\n김하나,91\n",
        encoding="utf-8",
    )

    kept, skipped = load_scores(str(csv_file))

    assert kept == [("김하나", 88), ("김하나", 91)]
    assert skipped == []


def test_빈_줄은_건너뛰고_건너뛴_목록에_기록하지_않는다(tmp_path):
    csv_file = tmp_path / "blank_line.csv"
    csv_file.write_text(
        "name,score\n김하나,88\n\n이두리,72\n",
        encoding="utf-8",
    )

    kept, skipped = load_scores(str(csv_file))

    assert kept == [("김하나", 88), ("이두리", 72)]
    assert skipped == []
