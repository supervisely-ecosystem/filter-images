<div align="center" markdown>

<img src="https://github.com/supervisely-ecosystem/filter-images/releases/download/v0.0.0/filter_poster.png" style="width: 100%;"/>

# Filter images

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-to-Use">How to Use</a> •
  <a href="#Screenshot">Screenshot</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/filter-images)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/filter-images)
[![views](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/filter-images&counter=views&label=views)](https://supervise.ly)
[![used by teams](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/filter-images&counter=downloads&label=used%20by%20teams)](https://supervise.ly)
[![runs](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/filter-images&counter=runs&label=runs&123)](https://supervise.ly)

</div>

# Overview

App filters images from a project and allows you to copy, move, delete images and assign or remove tags.

# How to Use

1. Select project and datasets

2. Select one from available filter presets or click 'Add filter' button

3. You can change way to filter if you need. Available ways:

- `By Filename`: select images where filename consists specified subsequence.
- `With tag`: select images with specified image tag.
- `Without tag`: select images without specified image tag.
- `Objects with tag`: select images containing specified number of objects with specified image tag.
- `Objects without tag`: select images containing specified number of objects without specified image tag.
- `Objects of class`: select images containing specified number of objects of specified class.
- `Objects by annotator`: select images containing specified number of objects annotated by specified annotator.
- `Tagged by annotator`: select images containing specified number of tags annotated by specified annotator.
- `With issues`: select images containing specified number of issues with specified status.

In addition, tag filter can be be configured with a specific value of tag or range of values (for numbers)

You can add as many filter as you need. Filters will be combined with logical AND rule.

4. Apply selected filters and explore the data in the table below.

5. Select one from available actions to apply to filtered data. Available actions:

- `Copy / Move`
- `Delete`
- `Assign tag`
- `Remove all tags`

6. Be sure that you are correctly selected action and destination project / dataset (in `Copy / Move` action). If everything is ok, apply selected action.

7. Check destination project that everything is ok. If you need to apply more actions, click `SELECT NEXT ACTION` button.

8. If you got all results that you wanted, click `FINISH APP` button.


Write to our technical support if you didn't find needed ways to filter your data.

# Screenshot

<img src="https://github.com/supervisely-ecosystem/filter-images/releases/download/v0.0.0/filter_screenshot.png" />