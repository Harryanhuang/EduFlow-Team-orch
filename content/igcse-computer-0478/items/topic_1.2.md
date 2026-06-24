# Topic 1.2 — Text, Sound and Images in Binary
## Items File

**Item 1 [F]**
Question: What is the main advantage of Unicode over ASCII?
Answer: Unicode uses 16 bits (or more) per character, allowing it to represent 65,536+ characters, whereas ASCII only uses 7 bits and can represent only 128 characters.
Difficulty: F
Topic: 1.2
Explanation: Unicode was developed to represent characters from all languages of the world, including symbols, emojis, and historical scripts, which ASCII cannot handle.
Tags: character encoding, Unicode, ASCII

**Item 2 [F]**
Question: A bitmap image has a resolution of 800 by 600 pixels. How many pixels does it contain in total?
Answer: 800 × 600 = 480,000 pixels.
Difficulty: F
Topic: 1.2
Explanation: Resolution is calculated by multiplying the width by the height in pixels. This gives the total number of individual picture elements.
Tags: bitmap images, resolution, pixels

**Item 3 [F]**
Question: What does "colour depth" mean in the context of bitmap images?
Answer: Colour depth is the number of bits used to represent the colour of each pixel. It determines how many distinct colours can be displayed.
Difficulty: F
Topic: 1.2
Explanation: Higher colour depth means more bits per pixel, which allows for a greater range of colours. For example, 1-bit gives 2 colours, 8-bit gives 256 colours, and 24-bit gives over 16 million colours.
Tags: bitmap images, colour depth, bit depth

**Item 4 [F]**
Question: A sound is sampled at 44,100 Hz. What does this mean?
Answer: It means 44,100 samples are taken per second.
Difficulty: F
Topic: 1.2
Explanation: Sampling rate (measured in Hertz) indicates how many amplitude measurements are captured each second. Higher rates capture more detail of the sound wave.
Tags: sound, sampling rate, audio

**Item 5 [F]**
Question: State one example of a lossless compression format and one example of a lossy compression format.
Answer: Lossless: PNG or GIF; Lossy: JPEG or MP3.
Difficulty: F
Topic: 1.2
Explanation: Lossless compression restores the original data perfectly when decompressed. Lossy compression achieves higher compression by permanently discarding some data that is deemed less perceptible.
Tags: data compression, lossless, lossy

**Item 6 [F]**
Question: Why is text stored in binary on a computer?
Answer: Because computers only understand two states: on (1) and off (0). Binary is the fundamental language of digital electronics.
Difficulty: F
Topic: 1.2
Explanation: All data types, including text, are ultimately stored as sequences of bits. Character encoding maps characters to binary codes so they can be stored and processed.
Tags: binary, text encoding, computer fundamentals

**Item 7 [S]**
Question: An image has 24-bit colour depth. Calculate how many distinct colours can be represented.
Answer: 2^24 = 16,777,216 colours.
Difficulty: S
Topic: 1.2
Explanation: Each bit doubles the number of possible values. With 24 bits, there are 2 raised to the power of 24 possible combinations, each representing a different colour.
Tags: bitmap images, colour depth, calculation

**Item 8 [S]**
Question: Explain why a 10-second recording at a higher sampling rate requires more storage than the same recording at a lower sampling rate.
Answer: Higher sampling rate means more samples are taken per second. Over 10 seconds, this results in more total samples, and since each sample requires a fixed number of bits, the overall file size is larger.
Difficulty: S
Topic: 1.2
Explanation: Storage requirement equals sampling rate multiplied by bit depth multiplied by duration. Doubling the sampling rate doubles the storage needed for the same length of audio.
Tags: sound, sampling rate, storage

**Item 9 [S]**
Question: Describe the difference between character encoding and the actual storage of images or sound.
Answer: Text uses character encoding schemes like ASCII or Unicode to map characters to numeric codes. Images and sound are stored as sampled data — images as pixel grids with colour values, and sound as a series of amplitude measurements.
Difficulty: S
Topic: 1.2
Explanation: Both ultimately become binary, but the data representation differs fundamentally. Text is symbolic and discrete, whereas images and sound are continuous analog signals that are discretised for digital storage.
Tags: character encoding, data representation, bitmap, sound

**Item 10 [S]**
Question: A bitmap image is 1600 by 1200 pixels with 16-bit colour depth. Calculate the minimum file size in megabytes.
Answer: 1600 × 1200 = 1,920,000 pixels. 1,920,000 × 16 bits = 30,720,000 bits = 3,840,000 bytes = 3.66 MB.
Difficulty: S
Topic: 1.2
Explanation: Multiply pixels by bits per pixel to get total bits, then divide by 8 for bytes and by 1,048,576 for megabytes.
Tags: bitmap images, file size calculation, colour depth

**Item 11 [S]**
Question: Why is GIF considered a lossless compression format while JPEG is considered lossy?
Answer: GIF uses lossless compression that preserves all original pixel data, which is why it is suitable for graphics with sharp edges and few colours. JPEG discards some image detail during compression to achieve smaller file sizes, making it irreversible.
Difficulty: S
Topic: 1.2
Explanation: The choice between formats depends on the content type. Photographs benefit from JPEG's lossy compression, while diagrams and logos should use PNG or GIF to avoid quality degradation.
Tags: data compression, lossless, lossy, image formats

**Item 12 [S]**
Question: What is the role of a sampling interval in digitising sound?
Answer: The sampling interval is the time gap between consecutive samples, equal to 1 divided by the sampling rate. It determines how accurately the digital version represents the original sound wave.
Difficulty: S
Topic: 1.2
Explanation: A smaller sampling interval (higher rate) captures higher-frequency sounds more accurately. According to the Nyquist theorem, the sampling rate must be at least twice the highest frequency to avoid distortion.
Tags: sound, sampling rate, digitisation

**Item 13 [C]**
Question: A photograph is stored in both PNG and JPEG formats at the same resolution. The JPEG file is significantly smaller. Explain, with reference to compression methods, why this is the case and identify a situation where the PNG format would still be preferred.
Answer: JPEG uses lossy compression that discards perceptual data (subtle colour variations and fine detail) to achieve smaller file sizes. PNG uses lossless compression that preserves all original pixel data. PNG is preferred when editing images repeatedly (avoiding cumulative quality loss), when transparent backgrounds are needed, or when text and sharp edges must remain crisp.
Difficulty: C
Topic: 1.2
Explanation: Lossy compression is asymmetric — each save discards data that cannot be recovered. For photographs intended for printing or repeated editing, PNG maintains fidelity across multiple save cycles.
Tags: data compression, lossless, lossy, image formats, PNG, JPEG

**Item 14 [C]**
Question: A developer needs to store a music track in a format suitable for a mobile app where storage space is limited. Evaluate whether MP3 or WAV would be the better choice and explain your reasoning.
Answer: MP3 would be the better choice because it uses lossy compression to achieve file sizes roughly 10-12 times smaller than uncompressed WAV files. WAV stores audio without any compression, preserving every sample. For a storage-limited mobile app, MP3 is practical. However, if the app requires professional audio editing or lossless playback, WAV or FLAC would be necessary despite the larger file sizes.
Difficulty: C
Topic: 1.2
Explanation: The decision involves a trade-off between storage efficiency and audio quality. MP3 at 128 kbps sacrifices some audible detail for compression; WAV at 44,100 Hz and 16-bit depth is CD-quality but occupies significant space.
Tags: sound, data compression, MP3, WAV, lossy

**Item 15 [C]**
Question: Discuss how increasing both the sampling rate and bit depth affects the quality and file size of digitised sound, and explain why there are practical limits to how high these values can be set.
Answer: Increasing sampling rate captures higher frequencies more accurately and reduces aliasing. Increasing bit depth increases dynamic range and reduces quantisation noise. Both changes increase file size proportionally. Practical limits exist because human hearing peaks around 20 kHz (setting Nyquist minimum at 40 kHz, standard 44.1 kHz), and 16-bit depth covers the audible dynamic range. Higher values produce improvements beyond human perception while consuming more storage and processing power.
Difficulty: C
Topic: 1.2
Explanation: The Nyquist theorem establishes the minimum sampling rate. Beyond certain thresholds, increases in sampling rate and bit depth yield diminishing returns in perceived quality. Industry standards (44.1 kHz, 16-bit) balance quality, compatibility, and storage efficiency.
Tags: sound, sampling rate, bit depth, Nyquist theorem, file size

**Item 16 [C]**
Question: Explain the process of converting a colour photograph into a bitmap image stored in binary, describing the role of resolution, colour depth, and compression.
Answer: The photograph is first scanned or captured at a specific resolution, determining the number of pixels. Each pixel's colour is then quantised according to the colour depth (e.g., 24-bit uses 8 bits each for red, green, and blue). The resulting pixel grid is stored as binary data. Compression is then applied — lossless compression reduces redundancy without data loss, while lossy compression discards less perceptible detail to achieve greater reduction.
Difficulty: C
Topic: 1.2
Explanation: This pipeline represents the complete digitisation process. Resolution affects spatial detail, colour depth affects tonal range, and compression affects storage efficiency. All three parameters affect the quality and size of the final image.
Tags: bitmap images, digitisation, resolution, colour depth, compression

**Item 17 [C]**
Question: A school database stores student names using ASCII while a multilingual website uses UTF-16. Compare the storage implications of these two encoding schemes for a dataset of 5,000 student names averaging 20 characters each.
Answer: ASCII stores each character in 1 byte (8 bits), so 5,000 names × 20 characters = 100,000 bytes (~98 KB). UTF-16 stores each character in 2 bytes (16 bits), so the same dataset would require 200,000 bytes (~195 KB) — roughly double. For primarily English text, ASCII is more efficient. UTF-16's overhead is justified when the text contains non-Latin scripts, but it wastes storage for pure ASCII content.
Difficulty: C
Topic: 1.2
Explanation: Variable-length encodings like UTF-8 avoid this issue by using 1 byte for ASCII-compatible characters and more bytes for others. However, UTF-16's fixed 2-byte representation simplifies processing for multilingual applications.
Tags: character encoding, ASCII, Unicode, UTF-16, storage

**Item 18 [C]**
Question: Evaluate the statement: "Lossy compression is always better than lossless compression for multimedia files on the internet."
Answer: This statement is false. Lossy compression is better only when significant size reduction is needed and some quality loss is acceptable. For line art, screenshots, or text within images, lossless formats like PNG preserve sharp edges that lossy JPEG compression would blur. For archival or professional audio work, WAV or FLAC are preferred to avoid irreversible quality degradation. The choice depends on the use case, acceptable quality level, and whether the file will be edited multiple times.
Difficulty: C
Topic: 1.2
Explanation: Lossy compression introduces artefacts that compound with each re-encoding. For images that will be cropped, adjusted, and re-saved, starting from a lossless original prevents generational quality loss. The internet speed versus quality trade-off varies by audience and application.
Tags: data compression, lossless, lossy, multimedia, evaluation
