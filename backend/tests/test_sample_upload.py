from eyrie_api.database.async_sample_operations import sample_upsert

UPLOAD = {
    'sample_id': 's1', 'lims_id': 'LIMS_s1', 'taxonomic_data': {'hits': []}, 'qc': 'unprocessed',
    'comments': {'qc': [], 'other': ''}, 'flagged_top_hits': [], 'flagged_contaminants': [], 'metadata': None,
}


def test_reupload_replaces_results_and_keeps_review_work_unless_reset():
    kept = sample_upsert(UPLOAD)
    assert set(kept['$set']) == {'taxonomic_data', 'updated_date'}
    assert set(kept['$setOnInsert']) == {'lims_id', 'qc', 'comments', 'flagged_top_hits', 'flagged_contaminants', 'metadata', 'created_date'}

    reset = sample_upsert(UPLOAD, reset_review=True)
    assert set(reset['$set']) == {'taxonomic_data', 'qc', 'comments', 'flagged_top_hits', 'flagged_contaminants', 'updated_date'}
    assert set(reset['$setOnInsert']) == {'lims_id', 'metadata', 'created_date'}
