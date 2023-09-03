# _ANC System Design Documentation_

---

## <a id="content">Content: </a>
1. <a href="overview">Overview. </a>
2. [Motivation.]()
3. [Sucess Metrics.]()
4. [Requirements and Constraints.]()
5. [Methodology.]()
6. [Implementation.]()
7. [Appendix.]()
8. [References.]()
9. [Glossary.]()

<br>

---

### <a id="overview"></a> 1. Overview:

The Adaptive Active Noise Cancellation (AANC) project tries to revolutionize noise cancellation approach in the car manufacturing industry. Traditionally, car manufacturers invest significant amount of money in hardware solutions (e.g. the overpriced microcontrollers that form the noise cancellation system inside the car) to insulate passengers from external noise, which can average between **70 to 80 dBs** during the highway drives.

Our solution offers a modern technical approach by leveraging machine learning algoritms within a mobile (or desktop) application. Passengers can simply connect their phones to the car's audio system and activate the AANC app. The application, using our developed neural network, assesses the ambient noise and sends an anti-signal to counteract the noise, aiming to reduce the in-car levels to more **comfortable 30 to 40 dBs**, enhancing the in-car drivers experience.

<p align="center">
<img src="./../../src/imgs/ANC_principle.png">
</p>

---



