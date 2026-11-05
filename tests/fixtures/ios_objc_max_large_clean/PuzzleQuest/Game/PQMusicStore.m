#import "PQMusicStore.h"

static NSString *const kKey = @"puzzlequest.music";

@implementation PQMusicStore

+ (instancetype)sharedStore
{
    static PQMusicStore *shared;
    static dispatch_once_t onceToken;
    dispatch_once(&onceToken, ^{
        shared = [[PQMusicStore alloc] init];
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
