# Backup and Recovery container images

![build](https://github.com/InformaticsMatters/bandr/workflows/build/badge.svg)
![build latest](https://github.com/InformaticsMatters/bandr/workflows/build%20latest/badge.svg)
![build tag](https://github.com/InformaticsMatters/bandr/workflows/build%20tag/badge.svg)
![build stable](https://github.com/InformaticsMatters/bandr/workflows/build%20stable/badge.svg)

![GitHub tag (latest SemVer)](https://img.shields.io/github/v/tag/informaticsmatters/bandr)

[![CodeFactor](https://www.codefactor.io/repository/github/informaticsmatters/bandr/badge)](https://www.codefactor.io/repository/github/informaticsmatters/bandr)

This project contains a backup container image definition that can be
used as a Kubernetes `CronJob` (or one-time `Job`) to backup a PostgreSQL
database using configurable hourly, daily, weekly and monthly strategies.

There is also a recovery image that can be used as a Kubernetes
`Job` in order to list and/or recover the latest backup or a specific
backup.

Images are built and published automatically using GitHub Actions.

>   The image is built with PostgreSQL 12.

>   For a detailed description of each utility refer to `backup.py` or
    `recovery.py`, where the operation and supported environment variables
    are explained.

Automated playbooks that use these images in Kubernetes deeployments
can be found in our [bandr-ansible] repository.

---

[bandr-ansible]: https://github.com/InformaticsMatters/bandr-ansible
