function crawlApp() {
    return {
        url: '',
        maxPages: 100,
        maxDepth: 5,
        showSettings: false,
        crawling: false,
        progressStatus: '',
        pagesCrawled: 0,
        currentUrl: '',
        progressPercent: 0,
        jobId: null,

        async startCrawl() {
            if (!this.url) return;
            this.crawling = true;
            this.progressStatus = 'Starting crawl...';

            try {
                const resp = await fetch('/api/crawl/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        url: this.url,
                        max_pages: this.maxPages,
                        max_depth: this.maxDepth,
                    }),
                });

                if (!resp.ok) throw new Error('Failed to start crawl');

                const job = await resp.json();
                this.jobId = job.id;
                this.listenProgress(job.id);
            } catch (e) {
                this.crawling = false;
                alert('Error: ' + e.message);
            }
        },

        listenProgress(jobId) {
            const evtSource = new EventSource(`/api/progress/${jobId}`);

            evtSource.addEventListener('progress', (e) => {
                const data = JSON.parse(e.data);
                this.progressStatus = data.status.charAt(0).toUpperCase() + data.status.slice(1);
                this.pagesCrawled = data.pages_crawled || 0;
                this.currentUrl = data.current_url || '';

                if (data.pages_found > 0) {
                    this.progressPercent = Math.min(95, (data.pages_crawled / data.pages_found) * 100);
                }

                if (data.status === 'analyzing') {
                    this.progressPercent = 95;
                    this.progressStatus = 'Analyzing pages...';
                }
            });

            evtSource.addEventListener('done', (e) => {
                evtSource.close();
                this.progressPercent = 100;
                this.progressStatus = 'Complete!';

                setTimeout(() => {
                    window.location.href = `/report/${jobId}`;
                }, 500);
            });

            evtSource.onerror = () => {
                evtSource.close();
                // Poll for completion
                this.pollStatus(jobId);
            };
        },

        async pollStatus(jobId) {
            const check = async () => {
                const resp = await fetch(`/api/crawl/${jobId}`);
                const job = await resp.json();

                if (job.status === 'complete') {
                    window.location.href = `/report/${jobId}`;
                } else if (job.status === 'failed') {
                    this.crawling = false;
                    alert('Crawl failed: ' + (job.error_message || 'Unknown error'));
                } else {
                    this.pagesCrawled = job.pages_crawled;
                    setTimeout(check, 2000);
                }
            };
            check();
        }
    };
}
