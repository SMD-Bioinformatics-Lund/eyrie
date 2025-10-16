db = db.getSiblingDB('eyrie');

db.createUser({
  user: 'admin',
  pwd: 'admin',
  roles: [
    {
      role: 'readWrite',
      db: 'eyrie'
    }
  ]
});

db.samples.insertMany([
  {
    sample_name: "Sample_001",
    sample_id: "S001",
    sequencing_run_id: "RUN_2024_001",
    lims_id: "LIMS_001",
    classification: "16S",
    qc: "passed",
    comments: "High quality sequencing data",
    created_date: new Date("2024-01-15"),
    updated_date: new Date("2024-01-15"),
    krona_file: "sample_001_krona.html",
    quality_plot: "sample_001_quality.html",
    pipeline_files: ["sample_001_report.html", "sample_001_stats.html"],
    statistics: {
      total_reads: 125432,
      quality_passed: 118204,
      avg_length: 287,
      avg_quality: 32.4
    },
    flagged_contaminants: [],
    flagged_top_hits: [],
    spike: null
  },
  {
    sample_name: "Sample_002",
    sample_id: "S002",
    sequencing_run_id: "RUN_2024_001",
    lims_id: "LIMS_002",
    classification: "ITS",
    qc: "failed",
    comments: "Low read count",
    created_date: new Date("2024-01-15"),
    updated_date: new Date("2024-01-16"),
    krona_file: "sample_002_krona.html",
    quality_plot: "sample_002_quality.html",
    pipeline_files: ["sample_002_report.html"],
    statistics: {
      total_reads: 45123,
      quality_passed: 32890,
      avg_length: 245,
      avg_quality: 28.1
    },
    flagged_contaminants: [],
    flagged_top_hits: [],
    spike: null
  },
  {
    sample_name: "Sample_003",
    sample_id: "S003",
    sequencing_run_id: "RUN_2024_002",
    lims_id: "LIMS_003",
    classification: "16S",
    qc: "unprocessed",
    comments: "",
    created_date: new Date("2024-01-16"),
    updated_date: new Date("2024-01-16"),
    krona_file: "sample_003_krona.html",
    quality_plot: "sample_003_quality.html",
    pipeline_files: [],
    statistics: {
      total_reads: 89567,
      quality_passed: 78234,
      avg_length: 301,
      avg_quality: 31.2
    },
    flagged_contaminants: [],
    flagged_top_hits: [],
    spike: null
  }
]);
