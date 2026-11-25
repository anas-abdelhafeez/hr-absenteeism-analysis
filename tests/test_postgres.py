"""Runs sql/queries.sql on a real PostgreSQL server (started temporarily) and compares with DuckDB."""
import os, pathlib, tempfile, pandas as pd, psycopg2, pytest
import analysis
ROOT = pathlib.Path(__file__).resolve().parents[1]; os.chdir(ROOT)
pgserver = pytest.importorskip('pgserver')

def test_same_numbers_on_postgresql():
    D = pd.read_csv('data/absences.csv'); Q = analysis.load_queries(); duck = analysis.run_duckdb(Q)
    with tempfile.TemporaryDirectory() as tmp:
        srv = pgserver.get_server(tmp, cleanup_mode='stop')
        con = psycopg2.connect(srv.get_uri()); cur = con.cursor()
        cur.execute('SELECT version()'); assert 'PostgreSQL' in cur.fetchone()[0]
        cols = ', '.join(f'{c} ' + ('TEXT' if D[c].dtype == object else 'NUMERIC') for c in D.columns)
        cur.execute(f'CREATE TABLE absences ({cols})')
        import io
        buf = io.StringIO(); D.to_csv(buf, index=False, header=False); buf.seek(0)
        cur.copy_expert("COPY absences FROM STDIN WITH (FORMAT csv, NULL '')", buf)
        for name, sql in Q.items():
            cur.execute(sql); pg = pd.DataFrame(cur.fetchall(), columns=[c[0] for c in cur.description])
            du = duck[name].reset_index(drop=True)
            pg = pg.apply(lambda col: pd.to_numeric(col, errors='ignore'))
            assert list(pg.columns) == list(du.columns), name
            for c in pg.columns:
                if pg[c].dtype == object and du[c].dtype == object: assert pg[c].astype(str).tolist() == du[c].astype(str).tolist(), (name, c)
                else: assert (pg[c].astype(float).round(1).values == du[c].astype(float).round(1).values).all(), (name, c)
        con.close(); srv.cleanup()
