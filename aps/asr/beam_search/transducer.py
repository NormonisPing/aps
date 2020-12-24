#!/usr/bin/env python

# Copyright 2019 Jian Wu
# License: Apache 2.0 (http://www.apache.org/licenses/LICENSE-2.0)
"""
Beam search for transducer based AM
"""
import torch as th
import torch.nn as nn
import torch.nn.functional as tf

from queue import PriorityQueue
from typing import Union, List, Dict, Optional


class Node(object):
    """
    Node for usage in best-first beam search
    """

    def __init__(self, score, stats):
        self.score = score
        self.stats = stats

    def __lt__(self, other):
        return self.score >= other.score


def _prep_nbest(container: Union[List, PriorityQueue],
                nbest: int,
                normalized: bool = True,
                blank: int = 0) -> List[Dict]:
    """
    Return nbest hypos from queue or list
    """
    # get nbest
    if isinstance(container, PriorityQueue):
        beam_hypos = []
        while not container.empty():
            node = container.get_nowait()
            trans = [t.item() for t in node.stats["trans"]]
            beam_hypos.append({"score": node.score, "trans": trans + [blank]})
    else:
        beam_hypos = container
    # return best
    nbest_hypos = sorted(beam_hypos,
                         key=lambda n: n["score"] / (len(n["trans"]) - 1
                                                     if normalized else 1),
                         reverse=True)
    return nbest_hypos[:nbest]


def greedy_search(decoder: nn.Module,
                  enc_out: th.Tensor,
                  blank: int = 0) -> List[Dict]:
    """
    Greedy search algorithm for RNN-T
    Args:
        enc_out: N x Ti x D
    """
    if blank < 0:
        raise RuntimeError(f"Invalid blank ID: {blank:d}")
    N, T, _ = enc_out.shape
    if N != 1:
        raise RuntimeError(
            f"Got batch size {N:d}, now only support one utterance")
    if not hasattr(decoder, "step"):
        raise RuntimeError("Function step should defined in decoder network")
    if not hasattr(decoder, "pred"):
        raise RuntimeError("Function pred should defined in decoder network")

    blk = th.tensor([[blank]], dtype=th.int64, device=enc_out.device)
    dec_out, hidden = decoder.step(blk)
    score = 0
    trans = []
    for t in range(T):
        # 1 x V
        prob = tf.log_softmax(decoder.pred(enc_out[:, t], dec_out)[0], dim=-1)
        best_prob, best_pred = th.max(prob, dim=-1)
        score += best_prob.item()
        # not blank
        if best_pred.item() != blank:
            dec_out, hidden = decoder.step(best_pred[None, ...], hidden=hidden)
            trans += [best_pred.item()]
    return [{"score": score, "trans": [blank] + trans + [blank]}]


def beam_search(decoder: nn.Module,
                enc_out: th.Tensor,
                lm: Optional[nn.Module] = None,
                lm_weight: float = 0,
                beam: int = 16,
                blank: int = 0,
                nbest: int = 8,
                normalized: bool = True) -> List[Dict]:
    """
    Beam search (best first) algorithm for RNN-T
    Args:
        enc_out: N(=1) x Ti x D
    """
    if blank < 0:
        raise RuntimeError(f"Invalid blank ID: {blank:d}")
    N, T, _ = enc_out.shape
    if N != 1:
        raise RuntimeError(
            f"Got batch size {N:d}, now only support one utterance")
    if not hasattr(decoder, "step"):
        raise RuntimeError("Function step should defined in decoder network")
    if not hasattr(decoder, "pred"):
        raise RuntimeError("Function pred should defined in decoder network")
    if beam > decoder.vocab_size:
        raise RuntimeError(f"Beam size({beam}) > vocabulary size")
    if lm and lm.vocab_size < decoder.vocab_size:
        raise RuntimeError("lm.vocab_size < am.vocab_size, "
                           "seems different dictionary is used")

    nbest = min(beam, nbest)

    dev = enc_out.device
    blk = th.tensor([[blank]], dtype=th.int64, device=dev)
    beam_queue = PriorityQueue()
    init_node = Node(0.0, {"trans": [blk], "hidden": None, "lm_state": None})
    beam_queue.put_nowait(init_node)

    _, T, _ = enc_out.shape
    for t in range(T):
        queue_t = beam_queue
        beam_queue = PriorityQueue()
        for _ in range(beam):
            # pop one (queue_t is updated)
            cur_node = queue_t.get_nowait()
            trans = cur_node.stats["trans"]
            # make a step
            # cur_inp = th.tensor([[trans[-1]]], dtype=th.int64, device=dev)
            dec_out, hidden = decoder.step(trans[-1],
                                           hidden=cur_node.stats["hidden"])
            # predition: 1 x V
            prob = tf.log_softmax(decoder.pred(enc_out[:, t], dec_out)[0],
                                  dim=-1).squeeze()

            # add terminal node (end with blank)
            score = cur_node.score + prob[blank].item()
            blank_node = Node(
                score, {
                    "trans": trans,
                    "lm_state": cur_node.stats["lm_state"],
                    "hidden": cur_node.stats["hidden"]
                })
            beam_queue.put_nowait(blank_node)

            lm_state = None
            if lm and t:
                # 1 x 1 x V (without blank)
                lm_prob, lm_state = lm(trans[-1], cur_node.stats["lm_state"])
                if blank != decoder.vocab_size - 1:
                    raise RuntimeError(
                        "Hard code for blank = self.vocab_size - 1 here")
                prob[:-1] += tf.log_softmax(lm_prob[:, -1].squeeze(),
                                            dim=-1) * lm_weight

            # extend other nodes
            topk_score, topk_index = th.topk(prob, beam + 1)
            topk = topk_index.tolist()
            for i in range(beam + 1 if blank in topk else beam):
                if topk[i] == blank:
                    continue
                score = cur_node.score + topk_score[i].item()
                node = Node(
                    score, {
                        "trans": trans + [topk_index[None, i][..., None]],
                        "hidden": hidden,
                        "lm_state": lm_state
                    })
                queue_t.put_nowait(node)

    return _prep_nbest(beam_queue, nbest, normalized=normalized, blank=blank)
