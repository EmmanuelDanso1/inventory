from datetime import datetime
from invent_app import db

class BenchmarkRun(db.Model):
    __tablename__ = 'benchmark_runs'

    id = db.Column(db.Integer, primary_key=True)
    run_at = db.Column(db.DateTime, default=datetime.utcnow)
    norm_items = db.Column(db.Integer)
    norm_transactions = db.Column(db.Integer)
    denorm_items = db.Column(db.Integer)
    denorm_transactions = db.Column(db.Integer)
    results_json = db.Column(db.Text)  # stores full results as JSON
    write_results_json = db.Column(db.Text)  # stores write benchmark results
    winner_summary = db.Column(db.String(50))  # e.g. "Normalized 4 vs Denormalized 2"

    def __repr__(self):
        return f'<BenchmarkRun {self.id} at {self.run_at}>'