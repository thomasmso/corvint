#import "PQSoundStore.h"

static NSString *const kKey = @"puzzlequest.sound";

@implementation PQSoundStore

+ (instancetype)sharedStore
{
    static PQSoundStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQSoundStore alloc] init];
    });
    return shared;
}

- (NSInteger)volume
{
    return [[NSUserDefaults standardUserDefaults] integerForKey:kKey];
}

- (void)setVolume:(NSInteger)value
{
    [[NSUserDefaults standardUserDefaults] setInteger:value forKey:kKey];
}

- (void)reset
{
    [[NSUserDefaults standardUserDefaults] removeObjectForKey:kKey];
}

@end
