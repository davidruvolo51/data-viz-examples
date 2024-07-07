# Marathon data

In this example, I used race results for the 2023 Valencia Marathon. The top 250 men and women finishers were selected in this dataset. In the charts below, I wanted to look at pace across the marathon by men and women to see how runners paced the race in relation to runners that podiumed.

Some notes about the charts:

- The 5 distance isn't included as the pace is always 0.
- The distance `META` is the last race segment (40k+)
- All time variables are binned to a fix date so that axes and data can be properly formatted. In this case, all values are fixed to the date of the marathon (03 December 2023).

```js
import * as Plot from "npm:@observablehq/plot";

const splits = FileAttachment("./data/marathon_splits.csv").csv();
```

```js

const podium = {1: '1st', 2: '2nd', 3: '3rd'} 

const splitsByRunner = splits
  .map((row) => {
    return {
      ...row,
      'PACE_DATETIME': new Date(`${row.PACE_DATETIME}Z`),
      'PODIUM': Object.keys(podium).includes(row.OFFICIAL_POSITION)
        ? podium[row.OFFICIAL_POSITION]
        : "OTHER"
    }
  });

const splitsForMen = splitsByRunner.filter((row) => row.GENDER === "M" && row.OFFICIAL_POSITION < 51)
const splitsForWomen = splitsByRunner.filter((row) => row.GENDER === "F" && row.OFFICIAL_POSITION < 51)

function splitsChart(data, width, height, minTime, maxTime) {
  const podiumRunners = data.filter((row) => row.OFFICIAL_POSITION <= 3)
  const nonPodiumRunners = data.filter((row) => row.OFFICIAL_POSITION > 3)
  
  return Plot.plot({ 
    height: height - 60,
    marginBottom: -10, 
    width: width,
    x: {
      label: null,
      domain: [
        // '5K',
        '10K',
        '15K',
        '20K',
        'Half',
        '25K',
        '30K',
        '35K',
        '40K',
        'META',
      ],
    },
    y: {
      label: 'Pace (mins)',
      domain: [minTime, maxTime],
      type: 'time',
      ticks: d3.utcSecond.every(10),
      tickFormat: d3.timeFormat('%M:%S'),
    },
    color: {
      legend: true,
      domain: ['1st', '2nd', '3rd', 'OTHER'],
      range: ['#FFD700', '#C0C0C0', '#CD7F32', '#7F7F7F']
    },
    marks: [
      Plot.ruleX([0]),
      Plot.ruleY([0]),
      Plot.lineY(
        nonPodiumRunners,
        {
          x: 'DISTANCE',
          y: 'PACE_DATETIME',
          z: 'RACE_NUMBER',
          stroke: 'PODIUM',
          strokeWidth: 1
        }
      ),
      Plot.lineY(
        podiumRunners,
        {
          x: 'DISTANCE',
          y: 'PACE_DATETIME',
          z: 'RACE_NUMBER',
          stroke: 'PODIUM',
          strokeWidth: 3
        }
      )
    ]
  })
}

```

### Pace by distance for the top 50 male runners

<div class="grid card" style="height: 350px">
    ${resize((width, height) => splitsChart(splitsForMen,width, height, new Date('2023-12-03T00:02:40Z'),
        new Date('2023-12-03T00:04:00Z')))}
</div>

### Pace by distance for the top 50 female runners
<div class="grid card" style="height: 350px">
    ${
      resize((width, height) => splitsChart(
        splitsForWomen,
        width,
        height,
        new Date('2023-12-03T00:03:00Z'),
        new Date('2023-12-03T00:04:00Z')
      ))
    }
</div>
