<div align="center" markdown>

<img src="https://user-images.githubusercontent.com/106374579/183614089-97ae7aa0-3b01-4635-9ab9-2ce8bb7dde7c.png"/>

# Filter images

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-to-Use">How to Use</a> •
  <a href="#Result-Project-Readme">Result Project Readme</a> •
  <a href="#Screenshot">Screenshot</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervisely.com/apps/supervisely-ecosystem/filter-images)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervisely.com/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/filter-images)
[![views](https://app.supervisely.com/img/badges/views/supervisely-ecosystem/filter-images.png)](https://supervisely.com)
[![runs](https://app.supervisely.com/img/badges/runs/supervisely-ecosystem/filter-images.png)](https://supervisely.com)

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
- `Remove all tags (from images)`
- `Remove specific tag (from images)`

6. Be sure that you are correctly selected action and destination project / dataset (in `Copy / Move` action). If everything is ok, apply selected action.

7. Check destination project that everything is ok. If you need to apply more actions, click `SELECT NEXT ACTION` button. You can see metadata with filtering information in destination project Readme (see Result Project Readme below)

8. If you got all results that you wanted, click `FINISH APP` button.

Write to our technical support if you didn't find needed ways to filter your data.

# Result Project Readme

After successful filtering, click on 'Info' tab of project (see screenshot).
Here you can see all applied filters and actions to your project.

<img src="https://user-images.githubusercontent.com/97401023/192784431-24353ca1-6502-4d5e-958f-87505443c7f8.png" />

# Screenshot

<img src="https://github.com/supervisely-ecosystem/filter-images/releases/download/v0.0.0/filter_screenshot.png" />
