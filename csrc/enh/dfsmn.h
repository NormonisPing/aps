// Copyright 2021 Jian Wu
// License: Apache 2.0 (http://www.apache.org/licenses/LICENSE-2.0)

#ifndef CSRC_ENH_DFSMN_H_
#define CSRC_ENH_DFSMN_H_

#include <memory>
#include <vector>

#include "base/pipeline.h"
#include "enh/time_frequency.h"

namespace aps {

// Match with Transformer model in aps/rt_sse/enh/dfsmn.py

class DfsmnNet : public TimeFrequencyNnet {
 public:
  explicit DfsmnNet(const TimeFrequencyNnetOptions &opts);

  virtual bool Process(const torch::Tensor &audio_chunk,
                       torch::Tensor *audio_enhan);

  virtual void Reset();

  virtual torch::Tensor Flush();

 private:
  int32_t lctx_, rctx_;
  torch::jit::script::Module nnet_, feature_;
  STFT stft_;
  StreamingTorchiSTFT istft_;
  std::unique_ptr<Context> feat_ctx_, stft_ctx_;

  torch::Tensor FeatureTransform(const torch::Tensor &stft);
  torch::Tensor SpeechEnhancement();
};

}  // namespace aps

#endif  // CSRC_ENH_DFSMN_H_
